use super::frame_allocator::{AllocatorError, FrameAllocator};

pub const PAGE_SIZE: u64 = 4096;
const ENTRY_COUNT: usize = 512;
const PRESENT: u64 = 1 << 0;
const WRITABLE: u64 = 1 << 1;
const USER: u64 = 1 << 2;
const HUGE_PAGE: u64 = 1 << 7;
const NO_EXECUTE: u64 = 1 << 63;
const ADDRESS_MASK: u64 = 0x000f_ffff_ffff_f000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PagePermissions {
    pub read: bool,
    pub write: bool,
    pub execute: bool,
    pub user: bool,
}

impl PagePermissions {
    pub const KERNEL_DATA: Self = Self { read: true, write: true, execute: false, user: false };
    pub const USER_CODE: Self = Self { read: true, write: false, execute: true, user: true };
    pub const USER_DATA: Self = Self { read: true, write: true, execute: false, user: true };

    fn validate(self) -> Result<(), PageTableError> {
        if !self.read { return Err(PageTableError::UnsupportedPermissions); }
        if self.write && self.execute { return Err(PageTableError::WriteExecuteViolation); }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AddressSpace { root_frame: u64, id: u64 }

impl AddressSpace {
    pub fn new(root_frame: u64, id: u64) -> Result<Self, PageTableError> {
        if root_frame % PAGE_SIZE != 0 || root_frame & !ADDRESS_MASK != 0 { return Err(PageTableError::InvalidPhysicalAddress); }
        Ok(Self { root_frame, id })
    }
    pub const fn root_frame(self) -> u64 { self.root_frame }
    pub const fn id(self) -> u64 { self.id }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Mapping { pub physical_address: u64, pub permissions: PagePermissions }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PageTableError {
    InvalidVirtualAddress,
    InvalidPhysicalAddress,
    UnalignedAddress,
    UnsupportedPermissions,
    WriteExecuteViolation,
    AlreadyMapped,
    NotMapped,
    HugePageEncountered,
    MetadataExhausted,
    MemoryUnavailable,
}

/// Page table storage supplied by either a direct physical mapping or a deterministic host test.
pub trait PageTableStore {
    fn allocate_table(&mut self) -> Result<u64, PageTableError>;
    fn read_entry(&self, table_frame: u64, index: usize) -> Result<u64, PageTableError>;
    fn write_entry(&mut self, table_frame: u64, index: usize, value: u64) -> Result<(), PageTableError>;
    fn release_table(&mut self, table_frame: u64) -> Result<(), PageTableError>;
}

/// Four-level x86_64 page-table operations over PML4 -> PDPT -> PD -> PT. Each instance owns one
/// root; processes receive separate roots, while the caller explicitly copies only shared kernel
/// mappings into a new root. This prevents accidentally sharing user mappings between processes.
pub struct PageTableManager<S> { store: S }

impl<S: PageTableStore> PageTableManager<S> {
    pub const fn new(store: S) -> Self { Self { store } }
    pub fn store(&self) -> &S { &self.store }
    pub fn store_mut(&mut self) -> &mut S { &mut self.store }

    pub fn create_address_space(&mut self, id: u64) -> Result<AddressSpace, PageTableError> {
        let root = self.store.allocate_table()?;
        AddressSpace::new(root, id)
    }

    pub fn map_4k(
        &mut self,
        address_space: AddressSpace,
        virtual_address: u64,
        physical_address: u64,
        permissions: PagePermissions,
    ) -> Result<(), PageTableError> {
        validate_page_addresses(virtual_address, physical_address)?;
        permissions.validate()?;
        let indexes = page_indexes(virtual_address);
        let mut table = address_space.root_frame;
        for index in indexes[..3].iter().copied() {
            let entry = self.store.read_entry(table, index)?;
            if entry & PRESENT == 0 {
                let child = self.store.allocate_table()?;
                let mut flags = PRESENT | WRITABLE;
                if permissions.user { flags |= USER; }
                self.store.write_entry(table, index, child | flags)?;
                table = child;
            } else {
                if entry & HUGE_PAGE != 0 { return Err(PageTableError::HugePageEncountered); }
                let mut parent_entry = entry;
                if permissions.user { parent_entry |= USER; }
                if permissions.write { parent_entry |= WRITABLE; }
                if parent_entry != entry { self.store.write_entry(table, index, parent_entry)?; }
                table = entry & ADDRESS_MASK;
            }
        }
        let leaf_index = indexes[3];
        if self.store.read_entry(table, leaf_index)? & PRESENT != 0 { return Err(PageTableError::AlreadyMapped); }
        let mut flags = PRESENT;
        if permissions.write { flags |= WRITABLE; }
        if permissions.user { flags |= USER; }
        if !permissions.execute { flags |= NO_EXECUTE; }
        self.store.write_entry(table, leaf_index, physical_address | flags)
    }

    pub fn unmap_4k(&mut self, address_space: AddressSpace, virtual_address: u64) -> Result<u64, PageTableError> {
        if !is_canonical(virtual_address) { return Err(PageTableError::InvalidVirtualAddress); }
        if virtual_address % PAGE_SIZE != 0 { return Err(PageTableError::UnalignedAddress); }
        let indexes = page_indexes(virtual_address);
        let mut table = address_space.root_frame;
        for index in indexes[..3].iter().copied() {
            let entry = self.store.read_entry(table, index)?;
            if entry & PRESENT == 0 { return Err(PageTableError::NotMapped); }
            if entry & HUGE_PAGE != 0 { return Err(PageTableError::HugePageEncountered); }
            table = entry & ADDRESS_MASK;
        }
        let leaf = self.store.read_entry(table, indexes[3])?;
        if leaf & PRESENT == 0 { return Err(PageTableError::NotMapped); }
        self.store.write_entry(table, indexes[3], 0)?;
        let tables = [address_space.root_frame, self.store.read_entry(address_space.root_frame, indexes[0])? & ADDRESS_MASK, 0, 0];
        let mut tables = tables;
        tables[2] = self.store.read_entry(tables[1], indexes[1])? & ADDRESS_MASK;
        tables[3] = table;
        for child_level in (1..=3).rev() {
            let child = tables[child_level];
            let mut empty = true;
            for entry_index in 0..ENTRY_COUNT {
                if self.store.read_entry(child, entry_index)? != 0 { empty = false; break; }
            }
            if !empty { break; }
            self.store.write_entry(tables[child_level - 1], indexes[child_level - 1], 0)?;
            self.store.release_table(child)?;
        }
        Ok(leaf & ADDRESS_MASK)
    }

    pub fn translate(&self, address_space: AddressSpace, virtual_address: u64) -> Result<Mapping, PageTableError> {
        if !is_canonical(virtual_address) { return Err(PageTableError::InvalidVirtualAddress); }
        let indexes = page_indexes(virtual_address);
        let mut table = address_space.root_frame;
        let mut user = true;
        let mut writable = true;
        let mut executable = true;
        for (level, index) in indexes.iter().copied().enumerate() {
            let entry = self.store.read_entry(table, index)?;
            if entry & PRESENT == 0 { return Err(PageTableError::NotMapped); }
            user &= entry & USER != 0;
            writable &= entry & WRITABLE != 0;
            executable &= entry & NO_EXECUTE == 0;
            if level < 3 {
                if entry & HUGE_PAGE != 0 { return Err(PageTableError::HugePageEncountered); }
                table = entry & ADDRESS_MASK;
            } else {
                let permissions = PagePermissions { read: true, write: writable, execute: executable, user };
                return Ok(Mapping { physical_address: (entry & ADDRESS_MASK) | (virtual_address & (PAGE_SIZE - 1)), permissions });
            }
        }
        Err(PageTableError::NotMapped)
    }
}

fn validate_page_addresses(virtual_address: u64, physical_address: u64) -> Result<(), PageTableError> {
    if !is_canonical(virtual_address) { return Err(PageTableError::InvalidVirtualAddress); }
    if virtual_address % PAGE_SIZE != 0 || physical_address % PAGE_SIZE != 0 { return Err(PageTableError::UnalignedAddress); }
    if physical_address & !ADDRESS_MASK != 0 { return Err(PageTableError::InvalidPhysicalAddress); }
    Ok(())
}

const fn is_canonical(address: u64) -> bool {
    let upper = address >> 48;
    if address & (1 << 47) == 0 { upper == 0 } else { upper == 0xffff }
}

const fn page_indexes(address: u64) -> [usize; 4] {
    [((address >> 39) & 0x1ff) as usize, ((address >> 30) & 0x1ff) as usize,
     ((address >> 21) & 0x1ff) as usize, ((address >> 12) & 0x1ff) as usize]
}

/// Direct-map storage backend for use when the bootloader has established a physical-memory
/// offset mapping. The caller must guarantee that every allocated frame is mapped at `offset +
/// physical_address`, and that the mapping is writable and valid for the backend's lifetime.
pub struct DirectMappedPageTableStore<'a, const N: usize> {
    offset: u64,
    allocator: &'a mut FrameAllocator<N>,
}

impl<'a, const N: usize> DirectMappedPageTableStore<'a, N> {
    /// # Safety
    /// `offset` must describe a writable direct map covering every frame returned by `allocator`.
    pub unsafe fn new(offset: u64, allocator: &'a mut FrameAllocator<N>) -> Self { Self { offset, allocator } }

    fn table_ptr(&self, frame: u64) -> Result<*mut u64, PageTableError> {
        if frame % PAGE_SIZE != 0 || frame & !ADDRESS_MASK != 0 { return Err(PageTableError::InvalidPhysicalAddress); }
        let virtual_address = self.offset.checked_add(frame).ok_or(PageTableError::MemoryUnavailable)?;
        Ok(virtual_address as *mut u64)
    }
}

impl<const N: usize> PageTableStore for DirectMappedPageTableStore<'_, N> {
    fn allocate_table(&mut self) -> Result<u64, PageTableError> {
        let frame = self.allocator.allocate().map_err(map_allocator_error)?;
        let table = self.table_ptr(frame.start_address())?;
        for index in 0..ENTRY_COUNT { unsafe { core::ptr::write_volatile(table.add(index), 0) }; }
        Ok(frame.start_address())
    }
    fn read_entry(&self, table_frame: u64, index: usize) -> Result<u64, PageTableError> {
        if index >= ENTRY_COUNT { return Err(PageTableError::MemoryUnavailable); }
        let table = self.table_ptr(table_frame)?;
        Ok(unsafe { core::ptr::read_volatile(table.add(index)) })
    }
    fn write_entry(&mut self, table_frame: u64, index: usize, value: u64) -> Result<(), PageTableError> {
        if index >= ENTRY_COUNT { return Err(PageTableError::MemoryUnavailable); }
        let table = self.table_ptr(table_frame)?;
        unsafe { core::ptr::write_volatile(table.add(index), value) };
        Ok(())
    }
    fn release_table(&mut self, table_frame: u64) -> Result<(), PageTableError> {
        let frame = super::frame_allocator::Frame::from_start_address(table_frame).ok_or(PageTableError::InvalidPhysicalAddress)?;
        self.allocator.release(frame).map_err(map_allocator_error)
    }
}

fn map_allocator_error(error: AllocatorError) -> PageTableError {
    match error { AllocatorError::MetadataFull => PageTableError::MetadataExhausted, _ => PageTableError::MemoryUnavailable }
}

/// Activate an address space by writing its PML4 frame into CR3. This is deliberately an unsafe
/// boundary because the caller must ensure mappings remain valid for all code/stack after the switch.
#[cfg(target_arch = "x86_64")]
pub unsafe fn activate(address_space: AddressSpace) {
    unsafe { core::arch::asm!("mov cr3, {}", in(reg) address_space.root_frame, options(nostack, preserves_flags)); }
}

#[cfg(test)]
mod tests {
    use super::*;
    struct MockStore { frames: [[u64; ENTRY_COUNT]; 16], used: [bool; 16] }
    impl MockStore {
        fn new() -> Self { Self { frames: [[0; ENTRY_COUNT]; 16], used: [false; 16] } }
        fn slot(frame: u64) -> Result<usize, PageTableError> {
            if frame < 0x1000 || frame % PAGE_SIZE != 0 { return Err(PageTableError::InvalidPhysicalAddress); }
            let index = (frame / PAGE_SIZE - 1) as usize;
            if index >= 16 { Err(PageTableError::MemoryUnavailable) } else { Ok(index) }
        }
    }
    impl PageTableStore for MockStore {
        fn allocate_table(&mut self) -> Result<u64, PageTableError> {
            let index = self.used.iter().position(|used| !used).ok_or(PageTableError::MetadataExhausted)?;
            self.used[index] = true;
            self.frames[index] = [0; ENTRY_COUNT];
            Ok((index as u64 + 1) * PAGE_SIZE)
        }
        fn read_entry(&self, table_frame: u64, index: usize) -> Result<u64, PageTableError> {
            if index >= ENTRY_COUNT { return Err(PageTableError::MemoryUnavailable); }
            Ok(self.frames[Self::slot(table_frame)?][index])
        }
        fn write_entry(&mut self, table_frame: u64, index: usize, value: u64) -> Result<(), PageTableError> {
            if index >= ENTRY_COUNT { return Err(PageTableError::MemoryUnavailable); }
            self.frames[Self::slot(table_frame)?][index] = value;
            Ok(())
        }
        fn release_table(&mut self, table_frame: u64) -> Result<(), PageTableError> {
            let slot = Self::slot(table_frame)?;
            self.used[slot] = false;
            self.frames[slot] = [0; ENTRY_COUNT];
            Ok(())
        }
    }

    #[test]
    fn maps_translates_and_unmaps_with_permissions() {
        let mut manager = PageTableManager::new(MockStore::new());
        let space = manager.create_address_space(7).unwrap();
        manager.map_4k(space, 0x4000_1000, 0x8000, PagePermissions::USER_DATA).unwrap();
        let mapping = manager.translate(space, 0x4000_1123).unwrap();
        assert_eq!(mapping.physical_address, 0x8123);
        assert_eq!(mapping.permissions, PagePermissions::USER_DATA);
        assert_eq!(manager.unmap_4k(space, 0x4000_1000), Ok(0x8000));
        assert_eq!(manager.translate(space, 0x4000_1000), Err(PageTableError::NotMapped));
    }

    #[test]
    fn independent_roots_isolate_process_mappings() {
        let mut manager = PageTableManager::new(MockStore::new());
        let first = manager.create_address_space(1).unwrap();
        let second = manager.create_address_space(2).unwrap();
        manager.map_4k(first, 0x1000, 0x9000, PagePermissions::USER_CODE).unwrap();
        assert_eq!(manager.translate(second, 0x1000), Err(PageTableError::NotMapped));
        assert_eq!(first.id(), 1);
        assert_ne!(first.root_frame(), second.root_frame());
    }

    #[test]
    fn rejects_wx_unaligned_noncanonical_and_duplicate_mappings() {
        let mut manager = PageTableManager::new(MockStore::new());
        let space = manager.create_address_space(1).unwrap();
        let wx = PagePermissions { read: true, write: true, execute: true, user: true };
        assert_eq!(manager.map_4k(space, 0x1000, 0x8000, wx), Err(PageTableError::WriteExecuteViolation));
        assert_eq!(manager.map_4k(space, 0x1001, 0x8000, PagePermissions::USER_CODE), Err(PageTableError::UnalignedAddress));
        assert_eq!(manager.map_4k(space, 0x0001_0000_0000_0000, 0x8000, PagePermissions::USER_CODE), Err(PageTableError::InvalidVirtualAddress));
        manager.map_4k(space, 0x1000, 0x8000, PagePermissions::USER_CODE).unwrap();
        assert_eq!(manager.map_4k(space, 0x1000, 0x9000, PagePermissions::USER_CODE), Err(PageTableError::AlreadyMapped));
    }
}
