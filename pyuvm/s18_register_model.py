from pyuvm import uvm_object
from pyuvm.s17_register_enumerations import *
from pyuvm.s14_15_python_sequences import uvm_sequencer
from pyuvm.s14_15_python_sequences import uvm_sequence
from pyuvm.s14_15_python_sequences import uvm_sequence_item
from pyuvm.error_classes import UVMFatalError


class uvm_reg(uvm_object):
    pass


class uvm_reg_adapter(uvm_object):
    pass


# 18.1.1 Class declaration
class uvm_reg_block(uvm_object):

    # 18.1.2.1
    # TODO Fix signature
    def __init__(self, name=""):
        super().__init__(name)
        self._regs = []
        self._maps = {}

    # 18.1.2.3 create_map
    def create_map(self,
                   name: str,
                   base_addr: uvm_reg_addr_t,
                   n_bytes: int,
                   endian: uvm_endianness_e,
                   byte_addressing: bool = True):
        self._maps[name] = uvm_reg_map(name)
        self._maps[name].configure(self,
                                   base_addr,
                                   n_bytes,
                                   endian,
                                   byte_addressing)
        return self._maps[name]

    # 18.1.3.7
    # TODO Fix signature
    def get_registers(self):
        return self._regs

    def _add_register(self, reg):
        self._regs.append(reg)


# 18.2.1 Class declaration
class uvm_reg_map(uvm_object):

    # 18.2.3.1
    def __init__(self, name="uvm_reg_map"):
        super().__init__(name)
        # block in which map is created and applied
        self._parent: uvm_reg_block = None
        # Base address of the map
        self._base_addr: uvm_reg_addr_t = None
        # Byte width of the bus on which this map is used
        self._n_bytes: int = None
        self._endian: uvm_endianness_e = None
        # Indicates whether address in the map are byte or word aligned
        # True: addresses are byte aligned
        # False: addresses are word aligned
        self._byte_addressing: bool = True
        self._regs = {}
        self._reg_by_name = {}
        self._reg_by_offset = {}
        self._rights_to_reg = {}
        self._reg_mapping = {}
        self._sequencer: uvm_sequencer = None
        self._adapter: uvm_reg_adapter = None
        self._submap = {}
        # used to keep track of parent map (if any)
        self._parent_map = None
        # Indicates if map is confiugred
        self._is_configured = False

    # 18.2.3.2
    # TODO Support binary and hex values for 'base_addr'
    def configure(self,
                  parent: uvm_reg_block,
                  base_addr: uvm_reg_addr_t,
                  n_bytes: int,
                  endian: uvm_endianness_e,
                  byte_addressing: bool = True):
        self._parent = parent
        self._base_addr = base_addr
        self._n_bytes = n_bytes
        self._endian = endian
        self._byte_addressing = byte_addressing
        self._is_configured = True

    # Method to check if provided address is aligned
    def __is_addr_aligned(self, addr: int) -> bool:
        if self._byte_addressing is False:
            # if Word aligned addr should be divisible by 4
            return addr % 4 == 0
        else:
            return True

    # 18.2.3.3
    # TODO add frontdoor
    def add_reg(self,
                reg: uvm_reg,
                offset: uvm_reg_addr_t,
                rights: str = "RW",
                unmapped: bool = False) -> None:
        # Check if register is alredy present in the map
        if reg.get_name() in self._reg_by_name.keys():
            raise UVMFatalError(
                f"reg:{reg.get_name()} already present")
        if offset in self._reg_by_offset.keys():
            raise UVMFatalError(f"""reg:{reg.get_name()} with
                offset:{offset} present""")
        # Check offset alignment
        if not self.__is_addr_aligned(offset):
            raise UVMFatalError("offset:{offset} is not word aligned")
        # If all checks are satisfied,
        # add the register in the internal data structures
        self._reg_by_name[reg.get_name()] = reg
        self._reg_by_offset[offset] = reg
        self._rights_to_reg[rights] = reg
        self._reg_mapping[reg.get_name()] = unmapped

    # TODO 18.2.3.4 add_mem

    # 18.2.3.5 add_submap
    def add_submap(self, child_map, offset: uvm_reg_addr_t) -> None:
        child_map_name = child_map.get_name()
        for map_name, map_dict in self._submap.items():
            if map_dict['name'] == child_map_name:
                raise UVMFatalError(f"""submap with
                name:{child_map.get_name()} already added""")
            if map_dict['offset'] == offset:
                raise UVMFatalError(f"""submap with offset:{offset}
                already added""")
        # Update map details if all checks are satisfied
        self._submap[child_map_name] = {}
        self._submap[child_map_name]['map'] = child_map
        self._submap[child_map_name]['offset'] = offset
        child_map._parent_map = self

    # 18.2.3.6 set_sequencer
    def set_sequencer(self,
                      sequencer: uvm_sequencer,
                      adapter: uvm_reg_adapter = None) -> None:
        self._sequencer = sequencer
        self._adapter = adapter

    # Method to check if there is a submap with name
    def __is_map_valid(self, map_name: str) -> bool:
        if map_name in self._submap.keys():
            if self._submap[map_name]['map'] is None:
                return False
            else:
                return True
        else:
            return False

    # 18.2.3.7 get_submap_offset
    def get_submap_offset(self, submap) -> uvm_reg_addr_t:
        map_name = submap.get_name()
        if self.__is_map_valid(map_name):
            return self._submap[map_name]['offset']
        else:
            return -1

    # 18.2.3.8 set_submap_offset
    def set_submap_offset(self, submap, offset) -> None:
        map_name = submap.get_name()
        if self.__is_map_valid(map_name):
            self._submap[map_name]['offset'] = offset

    # 18.2.3.9 set_base_addr
    def set_base_addr(self, offset: int) -> None:
        self._base_addr = offset

    # 18.2.3.10 reset
    def reset(self, kind: str = "SOFT") -> None:
        for reg_name, reg in self._reg_by_offset.items():
            reg.reset(kind)

    # 18.2.4.1 get_root_map
    def get_root_map(self):
        # Check if this map is root map
        if len(self._submap.keys()) == 0:
            return self
        # Else call get_root_map method of parent map
        else:
            return self._parent_map.get_root_map()

    # 18.2.4.2
    def get_parent(self):
        if self._is_configured:
            return self._parent
        else:
            raise UVMFatalError("Map not configured")

    # 18.2.4.3 get_parent_map
    def get_parent_map(self):
        if self._parent_map is not None:
            return self._parent_map
        else:
            return None

    # 18.2.4.4
    def get_base_addr(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER):
        if self._is_configured:
            return self._base_addr
        else:
            raise UVMFatalError("Map not configured")

    # 18.2.4.5 get_n_bytes
    # TODO, use hier to get the narrowest bus width in bus map hierarchy
    def get_n_bytes(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> int:
        if self._is_configured:
            return self._n_bytes
        else:
            raise UVMFatalError("Map not configured")

    # 18.2.4.11
    def get_registers(self):
        return list(self._reg_by_offset.values())

    # 18.2.4.17
    # TODO Fix signature
    # TODO Handle case where no register exists at offset
    def get_reg_by_offset(self, offset):
        if offset in self._reg_by_offset.keys():
            return self._reg_by_offset[offset]
        else:
            raise UVMFatalError(f"register with offset:0x{offset} not present")


# 18.4.1 Class declaration
class uvm_reg(uvm_object):

    # 18.3.2.1
    # TODO Fix signature
    def __init__(self, name=""):
        super().__init__(name)
        self._parent = None
        self._fields = []

    # 18.4.2.2
    def configure(self, parent):
        self._parent = parent
        parent._add_register(self)

    # 18.4.3.1
    def get_parent(self):
        return self._parent

    # 18.4.3.11
    # TODO Return fields in canonical order (LSB to MSB)
    def get_fields(self):
        return self._fields

    # TODO Add validation
    # - field not None
    # - field not already added
    # - field fits in reg
    # - field doesn't overlap with any other field
    # - etc.
    def _add_field(self, field):
        self._fields.append(field)


# 18.5.1 Class declaration
class uvm_reg_field(uvm_object):

    # 18.5.3.1
    def __init__(self, name='uvm_reg_field'):
        super().__init__(name)
        self._parent = None
        self._size = None
        self._lsb_pos = None
        self._access = None
        self._is_volatile = None
        self._reset = None

    # 18.5.3.2
    # TODO Fix signature
    def configure(self, parent, size, lsb_pos, access, is_volatile, reset):
        # TODO Add validation of arguments
        # TODO Support binary and hex values for 'reset'
        self._parent = parent
        parent._add_field(self)
        self._size = size
        self._lsb_pos = lsb_pos
        self._access = access
        self._is_volatile = is_volatile
        self._reset = reset

    # 18.5.4.1
    def get_parent(self):
        # TODO Check that 'configure' was called
        return self._parent

    # 18.5.4.2
    def get_lsb_pos(self):
        # TODO Check that 'configure' was called
        return self._lsb_pos

    # 18.5.4.3
    def get_n_bits(self):
        # TODO Check that 'configure' was called
        return self._size

    # 18.5.4.5
    def get_access(self):
        # TODO Check that 'configure' was called
        return self._access

    # 18.5.4.10
    def is_volatile(self):
        # TODO Check that 'configure' was called
        return self._is_volatile

    # 18.5.5.6
    def get_reset(self):
        # TODO Check that 'configure' was called
        return self._reset


# Implement uvm_reg_item, uvm_reg_bus_op and uvm_reg_adapter
# to avoid circular imports
# 19.1.1 uvm_reg_item
class uvm_reg_item(uvm_sequence_item):
    def __init__(self, name=""):
        super().__init__(name)
        self._element_kind: uvm_elem_kind_e = None
        self._kind: uvm_access_e = None
        self._data = []
        self._size: int = 0
        self._offset: uvm_reg_addr_t = 0
        self._status: uvm_status_e = None
        self._map: uvm_reg_map = None
        self._door: uvm_door_e = None
        self._parent_sequence: uvm_sequence = None
        self._priority: int = None
        self._extension: uvm_object = None
        self._backdoor_kind: str = ""

    # 19.1.1.2.1 Element kind
    def set_element_kind(self, element_kind: uvm_elem_kind_e) -> None:
        self._element_kind = element_kind

    def get_element_kind(self) -> uvm_elem_kind_e:
        return self._element_kind

    # 19.1.1.2.2 Element
    # Implementation not required since type can be inferred
    # using isinstance() method

    # 19.1.1.2.3 Kind
    def set_kind(self, kind: uvm_access_e) -> None:
        self._kind = kind

    def get_kind(self) -> uvm_access_e:
        return self._kind

    # 19.1.1.2.4 Data value
    def set_value(self, value: uvm_reg_data_t, idx: int = 0) -> None:
        self._data[idx] = value

    def get_value(self, idx: int = 0) -> uvm_reg_data_t:
        return self._data[idx]

    def set_value_size(self, sz: int) -> None:
        self._size = sz

    def get_value_size(self):
        return self._size

    def set_value_array(self, value: list = []) -> None:
        self._data = value

    def get_value_array(self) -> list:
        return self._data

    # 19.1.1.2.5 Offset
    def set_offset(self, offset: uvm_reg_addr_t) -> None:
        self._offset = offset

    def get_offset(self) -> uvm_reg_addr_t:
        return self._offset

    # 19.1.1.2.6 Status
    def set_status(self, status: uvm_status_e) -> None:
        self._status = status

    def get_status(self) -> uvm_status_e:
        return self._status

    # 19.1.1.2.8 Map
    def set_map(self, map: uvm_reg_map) -> None:
        self._map = map

    def get_map(self) -> uvm_reg_map:
        return self._map

    # 19.1.1.2.9 Door
    def set_door(self, door: uvm_door_e) -> None:
        self._door = door

    def get_door(self) -> uvm_door_e:
        return self._door

    # 19.1.1.2.10 Parent sequence
    def set_parent_sequence(self, parent: uvm_sequence) -> None:
        self._parent_sequence = parent

    def get_parent_sequence(self) -> uvm_sequence:
        return self._parent_sequence

    # 19.1.1.2.11 Priority
    def set_priority(self, value: int) -> None:
        self._priority = value

    def get_priority(self) -> int:
        return self._priority

    # 19.1.1.2.12 Extension
    def set_extension(self, extension: uvm_object) -> None:
        self._extension = extension

    def get_extension(self) -> uvm_object:
        return self._extension

    # 19.1.1.2.13 Backdoor kind
    def set_bd_kind(self, bd_kind: str) -> None:
        # Update only if path is BACKDOOR
        if self._door == uvm_door_e.UVM_BACKDOOR:
            self._backdoor_kind = bd_kind
        # Default vlaue of _backdoor_kind is set to empty string
        # as per spec
        else:
            pass

    def get_bd_kind(self) -> str:
        return self._backdoor_kind

    # 19.1.1.3.2 convert2string
    def __str__(self) -> str:
        return f"""
        name : {self.get_name()}
        element_kind : {self._element_kind}
        kind : {self._kind}
        data : {self._data}
        size : {self._size}
        offset : {self._offset}
        status : {self._status}
        map: {self._map}
        door : {self._door}
        parent : {self._parent_sequence}
        priority : {self._priority}
        extension : {self._extension}
        backdoor_kind : {self._backdoor_kind}
        """


# 19.1.2 uvm_reg_bus_op
class uvm_reg_bus_op():
    def __init__(self,
                 kind: uvm_access_e,
                 addr: uvm_reg_addr_t,
                 data: uvm_reg_data_t,
                 n_bits: int,
                 byte_en: uvm_reg_data_t,
                 status: uvm_status_e):
        self._kind = kind
        self._addr = addr
        self._data = data
        self._n_bits = n_bits
        self._byte_en = byte_en
        self._status = status

    def __str__(self):
        return f"""
        kind : {self._kind}
        addr : {self._addr}
        data : {self._data}
        n_bytes : {self._n_bits}
        byte_en : {self._byte_en}
        status : {self._status}
        """


# 19.2.1 uvm_reg_adapter
class uvm_reg_adapter(uvm_object):
    def __init__(self, name=''):
        super().__init__(name)
        self.byte_enable: bool = False
        self.provides_responses: bool = False
        self.parent_sequence: uvm_sequence = None
        self._reg_item: uvm_reg_item = None

    # 19.2.1.2.5 reg2bus
    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        raise UVMFatalError("This method needs to be implemented")

    # 19.2.1.2.6 bus2reg
    def bus2reg(self, bus_item: uvm_sequence_item) -> uvm_reg_bus_op:
        raise UVMFatalError("This method needs to be implemented")
