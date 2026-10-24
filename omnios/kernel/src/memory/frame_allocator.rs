pub const FRAME_SIZE: u64 = 4096;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Frame(u64);

impl Frame {
    pub const fn from_number(number: u64) -> Self { Self(number) }
    pub const fn from_start_address(address: u64) -> Option<Self> {
        if address % FRAME_SIZE == 0 { Some(Self(address / FRAME_SIZE)) } else { None }
    }
    pub const fn number(self) -> u64 { self.0 }
    pub const fn start_address(self) -> u64 { self.0 * FRAME_SIZE }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UefiRegion {
    pub start: u64,
    pub end: u64,
    pub kind: RegionKind,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RegionKind { Usable, Reserved }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct FrameRange { start: u64, count: u64 }

impl FrameRange {
    const fn end(self) -> u64 { self.start + self.count }
    const fn contains(self, frame: u64) -> bool { frame >= self.start && frame < self.end() }
}

#[derive(Clone, Copy)]
struct RangeSet<const N: usize> { entries: [Option<FrameRange>; N], len: usize }

impl<const N: usize> RangeSet<N> {
    const fn new() -> Self { Self { entries: [None; N], len: 0 } }

    fn can_insert(&self, range: FrameRange) -> bool {
        self.len < N || self.entries[..self.len].iter().flatten().any(|existing| {
            existing.end() >= range.start && range.end() >= existing.start
        })
    }

    fn insert(&mut self, mut range: FrameRange) -> Result<(), AllocatorError> {
        let mut index = 0;
        while index < self.len {
            let current = self.entries[index].expect("range set prefix is populated");
            if current.end() < range.start || range.end() < current.start {
                index += 1;
                continue;
            }
            let start = range.start.min(current.start);
            let end = range.end().max(current.end());
            range.start = start;
            range.count = end - range.start;
            self.remove_index(index);
            index = 0;
        }
        if self.len == N { return Err(AllocatorError::MetadataFull); }
        let insertion = self.entries[..self.len].partition_point(|entry| entry.unwrap().start < range.start);
        for slot in (insertion..self.len).rev() { self.entries[slot + 1] = self.entries[slot]; }
        self.entries[insertion] = Some(range);
        self.len += 1;
        Ok(())
    }

    fn contains(&self, frame: u64) -> bool {
        self.entries[..self.len].iter().flatten().any(|range| range.contains(frame))
    }

    fn remove_frame(&mut self, frame: u64) -> Result<(), AllocatorError> {
        let Some(index) = self.entries[..self.len].iter().position(|entry| entry.unwrap().contains(frame)) else {
            return Err(AllocatorError::FrameNotTracked);
        };
        let range = self.entries[index].unwrap();
        match (frame == range.start, frame + 1 == range.end()) {
            (true, true) => self.remove_index(index),
            (true, false) => { self.entries[index] = Some(FrameRange { start: frame + 1, count: range.count - 1 }); }
            (false, true) => { self.entries[index] = Some(FrameRange { count: range.count - 1, ..range }); }
            (false, false) => {
                if self.len == N { return Err(AllocatorError::MetadataFull); }
                self.entries[index] = Some(FrameRange { count: frame - range.start, ..range });
                let right = FrameRange { start: frame + 1, count: range.end() - frame - 1 };
                for slot in (index + 1..self.len).rev() { self.entries[slot + 1] = self.entries[slot]; }
                self.entries[index + 1] = Some(right);
                self.len += 1;
            }
        }
        Ok(())
    }

    fn remove_index(&mut self, index: usize) {
        for slot in index..self.len - 1 { self.entries[slot] = self.entries[slot + 1]; }
        self.len -= 1;
        self.entries[self.len] = None;
    }

    fn frame_count(&self) -> u64 { self.entries[..self.len].iter().flatten().map(|range| range.count).sum() }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AllocatorError { InvalidRegion, NoFreeFrames, FrameNotTracked, FrameAlreadyTracked, MetadataFull }

/// Fixed-capacity, allocation-free physical frame allocator. Only UEFI `Usable` regions enter the
/// free set; every allocated or explicitly reserved frame remains tracked in a separate range set.
pub struct FrameAllocator<const MAX_RANGES: usize> {
    free: RangeSet<MAX_RANGES>,
    allocated: RangeSet<MAX_RANGES>,
    reserved: RangeSet<MAX_RANGES>,
}

impl<const MAX_RANGES: usize> FrameAllocator<MAX_RANGES> {
    pub fn from_memory_map(regions: &[UefiRegion]) -> Result<Self, AllocatorError> {
        let mut allocator = Self { free: RangeSet::new(), allocated: RangeSet::new(), reserved: RangeSet::new() };
        for region in regions {
            if region.end < region.start { return Err(AllocatorError::InvalidRegion); }
            if region.kind != RegionKind::Usable || region.start == region.end { continue; }
            let first = region.start.checked_add(FRAME_SIZE - 1).ok_or(AllocatorError::InvalidRegion)? / FRAME_SIZE;
            let last = region.end / FRAME_SIZE;
            if first < last {
                allocator.free.insert(FrameRange { start: first, count: last - first })?;
            }
        }
        Ok(allocator)
    }

    /// Adapts the exact memory regions passed by bootloader_api. Its API marks bootloader-owned
    /// pages and firmware-reserved regions as non-usable, so only `Usable` ranges are admitted.
    pub fn from_boot_info(regions: &[bootloader_api::info::MemoryRegion]) -> Result<Self, AllocatorError> {
        let mut allocator = FrameAllocator::empty();
        for region in regions {
            if matches!(region.kind, bootloader_api::info::MemoryRegionKind::Usable) {
                allocator.add_usable_region(region.start, region.end)?;
            }
        }
        Ok(allocator)
    }

    fn empty() -> Self { Self { free: RangeSet::new(), allocated: RangeSet::new(), reserved: RangeSet::new() } }

    fn add_usable_region(&mut self, start: u64, end: u64) -> Result<(), AllocatorError> {
        if end < start { return Err(AllocatorError::InvalidRegion); }
        if start == end { return Ok(()); }
        let first = start.checked_add(FRAME_SIZE - 1).ok_or(AllocatorError::InvalidRegion)? / FRAME_SIZE;
        let last = end / FRAME_SIZE;
        if first < last { self.free.insert(FrameRange { start: first, count: last - first })?; }
        Ok(())
    }

    pub fn allocate(&mut self) -> Result<Frame, AllocatorError> {
        if self.free.len == 0 { return Err(AllocatorError::NoFreeFrames); }
        let frame = Frame(self.free.entries[0].unwrap().start);
        if !self.allocated.can_insert(FrameRange { start: frame.0, count: 1 }) { return Err(AllocatorError::MetadataFull); }
        self.free.remove_frame(frame.0)?;
        self.allocated.insert(FrameRange { start: frame.0, count: 1 })?;
        Ok(frame)
    }

    pub fn reserve(&mut self, frame: Frame) -> Result<(), AllocatorError> {
        if self.allocated.contains(frame.0) || self.reserved.contains(frame.0) { return Err(AllocatorError::FrameAlreadyTracked); }
        if !self.free.contains(frame.0) { return Err(AllocatorError::FrameNotTracked); }
        if !self.reserved.can_insert(FrameRange { start: frame.0, count: 1 }) { return Err(AllocatorError::MetadataFull); }
        self.free.remove_frame(frame.0)?;
        self.reserved.insert(FrameRange { start: frame.0, count: 1 })?;
        Ok(())
    }

    pub fn unreserve(&mut self, frame: Frame) -> Result<(), AllocatorError> {
        if !self.reserved.contains(frame.0) { return Err(AllocatorError::FrameNotTracked); }
        if !self.free.can_insert(FrameRange { start: frame.0, count: 1 }) { return Err(AllocatorError::MetadataFull); }
        self.reserved.remove_frame(frame.0)?;
        self.free.insert(FrameRange { start: frame.0, count: 1 })?;
        Ok(())
    }

    pub fn release(&mut self, frame: Frame) -> Result<(), AllocatorError> {
        if !self.allocated.contains(frame.0) { return Err(AllocatorError::FrameNotTracked); }
        if !self.free.can_insert(FrameRange { start: frame.0, count: 1 }) { return Err(AllocatorError::MetadataFull); }
        self.allocated.remove_frame(frame.0)?;
        self.free.insert(FrameRange { start: frame.0, count: 1 })?;
        Ok(())
    }

    pub fn is_allocated(&self, frame: Frame) -> bool { self.allocated.contains(frame.0) }
    pub fn is_reserved(&self, frame: Frame) -> bool { self.reserved.contains(frame.0) }
    pub fn free_count(&self) -> u64 { self.free.frame_count() }
    pub fn allocated_count(&self) -> u64 { self.allocated.frame_count() }
    pub fn reserved_count(&self) -> u64 { self.reserved.frame_count() }
}

#[cfg(test)]
mod tests {
    use super::*;

    const fn usable(start: u64, end: u64) -> UefiRegion { UefiRegion { start, end, kind: RegionKind::Usable } }

    #[test]
    fn aligns_usable_regions_and_excludes_reserved_regions() {
        let regions = [
            usable(0x1001, 0x6000),
            UefiRegion { start: 0x6000, end: 0xA000, kind: RegionKind::Reserved },
            usable(0xA000, 0xC000),
        ];
        let allocator = FrameAllocator::<8>::from_memory_map(&regions).unwrap();
        assert_eq!(allocator.free_count(), 6);
    }

    #[test]
    fn allocate_release_and_reallocate_tracks_each_frame() {
        let mut allocator = FrameAllocator::<8>::from_memory_map(&[usable(0x1000, 0x5000)]).unwrap();
        let first = allocator.allocate().unwrap();
        assert_eq!(first.start_address(), 0x1000);
        assert!(allocator.is_allocated(first));
        assert_eq!(allocator.free_count(), 3);
        allocator.release(first).unwrap();
        assert!(!allocator.is_allocated(first));
        assert_eq!(allocator.free_count(), 4);
        assert_eq!(allocator.allocate().unwrap(), first);
    }

    #[test]
    fn reservations_cannot_be_allocated_until_unreserved() {
        let mut allocator = FrameAllocator::<8>::from_memory_map(&[usable(0x1000, 0x4000)]).unwrap();
        let reserved = Frame::from_number(2);
        allocator.reserve(reserved).unwrap();
        assert!(allocator.is_reserved(reserved));
        assert_eq!(allocator.reserved_count(), 1);
        allocator.unreserve(reserved).unwrap();
        assert!(!allocator.is_reserved(reserved));
        assert_eq!(allocator.free_count(), 3);
    }

    #[test]
    fn invalid_double_free_and_non_usable_reservation_are_rejected() {
        let mut allocator = FrameAllocator::<8>::from_memory_map(&[usable(0x1000, 0x2000)]).unwrap();
        let frame = allocator.allocate().unwrap();
        allocator.release(frame).unwrap();
        assert_eq!(allocator.release(frame), Err(AllocatorError::FrameNotTracked));
        assert_eq!(allocator.reserve(Frame::from_number(99)), Err(AllocatorError::FrameNotTracked));
    }

    #[test]
    fn interior_removals_split_ranges_without_losing_neighbors() {
        let mut allocator = FrameAllocator::<8>::from_memory_map(&[usable(0x1000, 0x6000)]).unwrap();
        allocator.reserve(Frame::from_number(3)).unwrap();
        assert_eq!(allocator.free_count(), 4);
        assert_eq!(allocator.allocate().unwrap(), Frame::from_number(1));
        assert_eq!(allocator.allocate().unwrap(), Frame::from_number(2));
        assert_eq!(allocator.allocate().unwrap(), Frame::from_number(4));
    }
}
