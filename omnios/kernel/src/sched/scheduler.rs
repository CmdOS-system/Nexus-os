use core::array;

const BASE_WEIGHT: u64 = 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Personality { LinuxPOSIX, WinNT, MachO, AndroidDEX, WASI }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TaskState { Runnable, Blocked, Exited }

/// Complete general-purpose register snapshot for a x86_64 interrupt-return context. The IDT
/// entry/epilogue must save fields in this exact order and return through the saved iret frame.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
#[repr(C)]
pub struct CpuContext {
    pub r15: u64, pub r14: u64, pub r13: u64, pub r12: u64,
    pub r11: u64, pub r10: u64, pub r9: u64, pub r8: u64,
    pub rsi: u64, pub rdi: u64, pub rbp: u64, pub rdx: u64,
    pub rcx: u64, pub rbx: u64, pub rax: u64,
    pub rip: u64, pub cs: u64, pub rflags: u64, pub rsp: u64, pub ss: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TaskStruct {
    pub id: u64,
    pub context: CpuContext,
    pub personality: Personality,
    pub state: TaskState,
    pub vruntime: u64,
    pub weight: u64,
    pub runtime_ticks: u64,
}

impl TaskStruct {
    pub const fn new(id: u64, context: CpuContext, personality: Personality) -> Self {
        Self { id, context, personality, state: TaskState::Runnable, vruntime: 0, weight: BASE_WEIGHT, runtime_ticks: 0 }
    }

    pub fn set_weight(&mut self, weight: u64) { self.weight = weight.max(1); }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SchedulingPolicy { RoundRobin, Fair }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ScheduleReason { TimerPreemption, Yield, Block, Exit }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SchedulerError { Full, DuplicateTaskId, UnknownTask, NoRunnableTask }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SwitchDecision { pub previous: Option<u64>, pub next: u64, pub context: CpuContext }

/// Fixed-capacity preemptive scheduler core. A timer/interrupt handler passes its saved machine
/// context here and restores the returned context before the interrupt-return instruction.
/// Round-robin rotates runnable tasks; Fair is a small weighted-vruntime policy (lower runtime wins).
pub struct Scheduler<const MAX_TASKS: usize> {
    tasks: [Option<TaskStruct>; MAX_TASKS],
    policy: SchedulingPolicy,
    last_selected: Option<usize>,
}

impl<const MAX_TASKS: usize> Scheduler<MAX_TASKS> {
    pub fn new(policy: SchedulingPolicy) -> Self {
        Self { tasks: array::from_fn(|_| None), policy, last_selected: None }
    }

    pub fn add_task(&mut self, task: TaskStruct) -> Result<(), SchedulerError> {
        if self.tasks.iter().flatten().any(|existing| existing.id == task.id) { return Err(SchedulerError::DuplicateTaskId); }
        let slot = self.tasks.iter_mut().find(|entry| entry.is_none()).ok_or(SchedulerError::Full)?;
        *slot = Some(task);
        Ok(())
    }

    pub fn task(&self, id: u64) -> Option<&TaskStruct> { self.tasks.iter().flatten().find(|task| task.id == id) }
    pub fn task_mut(&mut self, id: u64) -> Option<&mut TaskStruct> { self.tasks.iter_mut().flatten().find(|task| task.id == id) }
    pub fn runnable_count(&self) -> usize { self.tasks.iter().flatten().filter(|task| task.state == TaskState::Runnable).count() }

    pub fn schedule(
        &mut self,
        current_id: Option<u64>,
        saved_context: Option<CpuContext>,
        elapsed_ticks: u64,
        reason: ScheduleReason,
    ) -> Result<SwitchDecision, SchedulerError> {
        let previous_index = if let Some(id) = current_id {
            let index = self.find_task_index(id).ok_or(SchedulerError::UnknownTask)?;
            let task = self.tasks[index].as_mut().unwrap();
            if let Some(context) = saved_context { task.context = context; }
            if task.state == TaskState::Runnable {
                task.runtime_ticks = task.runtime_ticks.saturating_add(elapsed_ticks);
                let weighted = elapsed_ticks.saturating_mul(BASE_WEIGHT) / task.weight.max(1);
                let minimum_delta = if elapsed_ticks > 0 { 1 } else { 0 };
                task.vruntime = task.vruntime.saturating_add(weighted.max(minimum_delta));
            }
            match reason {
                ScheduleReason::Block => task.state = TaskState::Blocked,
                ScheduleReason::Exit => task.state = TaskState::Exited,
                ScheduleReason::TimerPreemption | ScheduleReason::Yield => {}
            }
            Some(index)
        } else { None };

        let next_index = match self.policy {
            SchedulingPolicy::RoundRobin => self.select_round_robin(previous_index),
            SchedulingPolicy::Fair => self.select_fair(),
        }.ok_or(SchedulerError::NoRunnableTask)?;
        self.last_selected = Some(next_index);
        let next = self.tasks[next_index].unwrap();
        Ok(SwitchDecision { previous: current_id, next: next.id, context: next.context })
    }

    fn find_task_index(&self, id: u64) -> Option<usize> { self.tasks.iter().position(|task| task.is_some_and(|task| task.id == id)) }

    fn select_round_robin(&self, previous: Option<usize>) -> Option<usize> {
        if MAX_TASKS == 0 { return None; }
        let start = previous.or(self.last_selected).map_or(0, |index| (index + 1) % MAX_TASKS);
        (0..MAX_TASKS).map(|offset| (start + offset) % MAX_TASKS)
            .find(|index| self.tasks[*index].is_some_and(|task| task.state == TaskState::Runnable))
    }

    fn select_fair(&self) -> Option<usize> {
        self.tasks.iter().enumerate().filter_map(|(index, entry)| entry
            .filter(|task| task.state == TaskState::Runnable)
            .map(|task| (index, task.vruntime)))
            .min_by_key(|(_, vruntime)| *vruntime).map(|(index, _)| index)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn task(id: u64, personality: Personality, rip: u64) -> TaskStruct {
        TaskStruct::new(id, CpuContext { rip, ..CpuContext::default() }, personality)
    }

    #[test]
    fn round_robin_saves_register_context_and_switches() {
        let mut scheduler = Scheduler::<4>::new(SchedulingPolicy::RoundRobin);
        scheduler.add_task(task(1, Personality::LinuxPOSIX, 0x1000)).unwrap();
        scheduler.add_task(task(2, Personality::WinNT, 0x2000)).unwrap();
        let saved = CpuContext { rip: 0x1010, rax: 0xfeed, ..CpuContext::default() };
        let decision = scheduler.schedule(Some(1), Some(saved), 1, ScheduleReason::TimerPreemption).unwrap();
        assert_eq!(decision.next, 2);
        assert_eq!(scheduler.task(1).unwrap().context, saved);
        assert_eq!(scheduler.task(1).unwrap().runtime_ticks, 1);
    }

    #[test]
    fn blocked_and_exited_tasks_are_not_selected() {
        let mut scheduler = Scheduler::<3>::new(SchedulingPolicy::RoundRobin);
        scheduler.add_task(task(10, Personality::MachO, 0x10)).unwrap();
        scheduler.add_task(task(11, Personality::AndroidDEX, 0x11)).unwrap();
        scheduler.add_task(task(12, Personality::WASI, 0x12)).unwrap();
        assert_eq!(scheduler.schedule(Some(10), None, 0, ScheduleReason::Block).unwrap().next, 11);
        assert_eq!(scheduler.schedule(Some(11), None, 0, ScheduleReason::Exit).unwrap().next, 12);
        assert_eq!(scheduler.task(10).unwrap().state, TaskState::Blocked);
        assert_eq!(scheduler.task(11).unwrap().state, TaskState::Exited);
    }

    #[test]
    fn fair_policy_selects_lowest_weighted_virtual_runtime() {
        let mut scheduler = Scheduler::<2>::new(SchedulingPolicy::Fair);
        scheduler.add_task(task(1, Personality::LinuxPOSIX, 0x1000)).unwrap();
        scheduler.add_task(task(2, Personality::WASI, 0x2000)).unwrap();
        scheduler.task_mut(1).unwrap().vruntime = 200;
        scheduler.task_mut(2).unwrap().vruntime = 10;
        assert_eq!(scheduler.schedule(None, None, 0, ScheduleReason::TimerPreemption).unwrap().next, 2);
    }

    #[test]
    fn task_personality_is_preserved_and_task_capacity_is_enforced() {
        let mut scheduler = Scheduler::<1>::new(SchedulingPolicy::RoundRobin);
        scheduler.add_task(task(4, Personality::AndroidDEX, 0x4000)).unwrap();
        assert_eq!(scheduler.task(4).unwrap().personality, Personality::AndroidDEX);
        assert_eq!(scheduler.add_task(task(4, Personality::WASI, 0)), Err(SchedulerError::DuplicateTaskId));
        assert_eq!(scheduler.add_task(task(5, Personality::WinNT, 0)), Err(SchedulerError::Full));
    }
}
