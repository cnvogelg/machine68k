import pytest
from machine68k import Memory, MemoryError, Machine, CPUType


@pytest.fixture(params=["mem", "local", "remote"])
def mem(request):
    mode = request.param
    if mode == "mem":
        yield Memory(16)
    elif mode == "local":
        m = Machine(CPUType.M68000, 16)
        yield m.mem
        m.cleanup()
    else:
        rmachine68k = pytest.importorskip("rmachine68k")
        client = request.getfixturevalue("remote_client")
        m = rmachine68k.create_machine(client, "68000", 16)
        yield m.mem


def machine68k_mem_size_test(mem):
    assert mem.get_ram_size_kib() == 16
    assert mem.get_ram_size_bytes() == 16 * 1024
    assert repr(mem) == "Memory(ram_size_kib=16)"


def machine68k_mem_rw_test(mem):
    assert mem.get_ram_size_kib() == 16

    mem.w8(0x100, 42)
    assert mem.r8(0x100) == 42

    mem.w16(0x200, 0xDEAD)
    assert mem.r16(0x200) == 0xDEAD

    mem.w32(0x300, 0xCAFEBABE)
    assert mem.r32(0x300) == 0xCAFEBABE

    mem.write(0, 0x101, 43)
    assert mem.read(0, 0x101) == 43

    mem.write(1, 0x202, 0x1234)
    assert mem.read(1, 0x202) == 0x1234

    mem.write(2, 0x304, 0x11223344)
    assert mem.read(2, 0x304) == 0x11223344

    # invalid values
    with pytest.raises(OverflowError):
        mem.w8(0x100, 0x100)
    with pytest.raises(OverflowError):
        mem.w8(0x100, -1)
    # invalid values
    with pytest.raises(OverflowError):
        mem.w16(0x100, 0x10000)
    with pytest.raises(OverflowError):
        mem.w16(0x100, -2)
    # invalid values
    with pytest.raises(OverflowError):
        mem.w32(0x100, 0x100000000)
    with pytest.raises(OverflowError):
        mem.w32(0x100, -3)
    # invalid type
    with pytest.raises(TypeError):
        mem.w8(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.w16(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.w32(0x100, "hello")
    # invalid width
    with pytest.raises(ValueError):
        mem.write(7, 0x202, 12)
    with pytest.raises(ValueError):
        mem.read(7, 0x202)

    # out of range
    with pytest.raises(MemoryError):
        mem.w8(0x10000, 0)
    with pytest.raises(MemoryError):
        mem.w16(0x10000, 0)
    with pytest.raises(MemoryError):
        mem.w32(0x10000, 0)
    with pytest.raises(MemoryError):
        mem.write(0, 0x10000, 0)
    with pytest.raises(MemoryError):
        mem.r8(0x10000)
    with pytest.raises(MemoryError):
        mem.r16(0x10000)
    with pytest.raises(MemoryError):
        mem.r32(0x10000)
    with pytest.raises(MemoryError):
        mem.read(0, 0x10000)


def machine68k_mem_rws_test(mem):
    mem.w8s(0x100, 42)
    assert mem.r8s(0x100) == 42
    mem.w8s(0x100, -23)
    assert mem.r8s(0x100) == -23

    mem.w16s(0x200, 0x7EAD)
    assert mem.r16s(0x200) == 0x7EAD
    mem.w16s(0x200, -0x1000)
    assert mem.r16s(0x200) == -0x1000

    mem.w32s(0x300, 0x1AFEBABE)
    assert mem.r32s(0x300) == 0x1AFEBABE
    mem.w32s(0x300, -0xAFEBABE)
    assert mem.r32s(0x300) == -0xAFEBABE

    mem.writes(0, 0x101, -43)
    assert mem.reads(0, 0x101) == -43
    mem.writes(1, 0x202, -0x1234)
    assert mem.reads(1, 0x202) == -0x1234
    mem.writes(2, 0x304, -0x11223344)
    assert mem.reads(2, 0x304) == -0x11223344

    # invalid values
    with pytest.raises(OverflowError):
        mem.w8s(0x100, 0x80)
    with pytest.raises(OverflowError):
        mem.w8s(0x100, -0x81)
    # invalid values
    with pytest.raises(OverflowError):
        mem.w16s(0x100, 0x8000)
    with pytest.raises(OverflowError):
        mem.w16s(0x100, -0x8001)
    # invalid values
    with pytest.raises(OverflowError):
        mem.w32s(0x100, 0x80000000)
    with pytest.raises(OverflowError):
        mem.w32s(0x100, -0x80000001)
    # invalid type
    with pytest.raises(TypeError):
        mem.w8s(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.w16s(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.w32s(0x100, "hello")
    # invalid width
    with pytest.raises(ValueError):
        mem.writes(7, 0x202, 12)
    with pytest.raises(ValueError):
        mem.reads(7, 0x202)

    # out of range
    with pytest.raises(MemoryError):
        mem.w8s(0x10000, 0)
    with pytest.raises(MemoryError):
        mem.w16s(0x10000, 0)
    with pytest.raises(MemoryError):
        mem.w32s(0x10000, 0)
    with pytest.raises(MemoryError):
        mem.writes(0, 0x10000, 0)
    with pytest.raises(MemoryError):
        mem.r8s(0x10000)
    with pytest.raises(MemoryError):
        mem.r16s(0x10000)
    with pytest.raises(MemoryError):
        mem.r32s(0x10000)
    with pytest.raises(MemoryError):
        mem.reads(0, 0x10000)


class InvalidMemAccess(object):
    def __init__(self, mem, mode, width, addr):
        self.mem = mem
        self.want = (mode, width, addr)

    def __enter__(self):
        self.mem.set_invalid_func(self.invalid_func)
        self.match = None
        return self

    def __exit__(self, type, value, traceback):
        self.mem.set_invalid_func(None)
        assert self.match == self.want

    def invalid_func(self, mode, width, addr):
        self.match = (mode, width, addr)


def machine68k_mem_cpu_rw_test(mem):
    assert mem.get_ram_size_kib() == 16

    mem.cpu_w8(0x100, 42)
    assert mem.cpu_r8(0x100) == 42

    mem.cpu_w16(0x200, 0xDEAD)
    assert mem.cpu_r16(0x200) == 0xDEAD

    mem.cpu_w32(0x300, 0xCAFEBABE)
    assert mem.cpu_r32(0x300) == 0xCAFEBABE

    # invalid values
    with pytest.raises(OverflowError):
        mem.cpu_w8(0x100, 0x100)
    with pytest.raises(OverflowError):
        mem.cpu_w8(0x100, -1)
    # invalid values
    with pytest.raises(OverflowError):
        mem.cpu_w16(0x100, 0x10000)
    with pytest.raises(OverflowError):
        mem.cpu_w16(0x100, -2)
    # invalid values
    with pytest.raises(OverflowError):
        mem.cpu_w32(0x100, 0x100000000)
    with pytest.raises(OverflowError):
        mem.cpu_w32(0x100, -3)
    # invalid type
    with pytest.raises(TypeError):
        mem.cpu_w8(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.cpu_w16(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.cpu_w32(0x100, "hello")

    # out of range
    with InvalidMemAccess(mem, "W", 0, 0x10000):
        mem.cpu_w8(0x10000, 0)
    with InvalidMemAccess(mem, "W", 1, 0x10000):
        mem.cpu_w16(0x10000, 0)
    with InvalidMemAccess(mem, "W", 2, 0x10000):
        mem.cpu_w32(0x10000, 0)
    with InvalidMemAccess(mem, "R", 0, 0x10000):
        mem.cpu_r8(0x10000)
    with InvalidMemAccess(mem, "R", 1, 0x10000):
        mem.cpu_r16(0x10000)
    with InvalidMemAccess(mem, "R", 2, 0x10000):
        mem.cpu_r32(0x10000)


def machine68k_mem_cpu_rws_test(mem):
    mem.cpu_w8s(0x100, 42)
    assert mem.cpu_r8s(0x100) == 42
    mem.cpu_w8s(0x100, -23)
    assert mem.cpu_r8s(0x100) == -23

    mem.cpu_w16s(0x200, 0x7EAD)
    assert mem.cpu_r16s(0x200) == 0x7EAD
    mem.cpu_w16s(0x200, -0x1000)
    assert mem.cpu_r16s(0x200) == -0x1000

    mem.cpu_w32s(0x300, 0x1AFEBABE)
    assert mem.cpu_r32s(0x300) == 0x1AFEBABE
    mem.cpu_w32s(0x300, -0xAFEBABE)
    assert mem.cpu_r32s(0x300) == -0xAFEBABE

    # invalid values
    with pytest.raises(OverflowError):
        mem.cpu_w8s(0x100, 0x80)
    with pytest.raises(OverflowError):
        mem.cpu_w8s(0x100, -0x81)
    # invalid values
    with pytest.raises(OverflowError):
        mem.cpu_w16s(0x100, 0x8000)
    with pytest.raises(OverflowError):
        mem.cpu_w16s(0x100, -0x8001)
    # invalid values
    with pytest.raises(OverflowError):
        mem.cpu_w32s(0x100, 0x80000000)
    with pytest.raises(OverflowError):
        mem.cpu_w32s(0x100, -0x80000001)
    # invalid type
    with pytest.raises(TypeError):
        mem.cpu_w8s(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.cpu_w16s(0x100, "hello")
    # invalid type
    with pytest.raises(TypeError):
        mem.cpu_w32s(0x100, "hello")

    # out of range
    with InvalidMemAccess(mem, "W", 0, 0x10000):
        mem.cpu_w8s(0x10000, 0)
    with InvalidMemAccess(mem, "W", 1, 0x10000):
        mem.cpu_w16s(0x10000, 0)
    with InvalidMemAccess(mem, "W", 2, 0x10000):
        mem.cpu_w32s(0x10000, 0)
    with InvalidMemAccess(mem, "R", 0, 0x10000):
        mem.cpu_r8s(0x10000)
    with InvalidMemAccess(mem, "R", 1, 0x10000):
        mem.cpu_r16s(0x10000)
    with InvalidMemAccess(mem, "R", 2, 0x10000):
        mem.cpu_r32s(0x10000)


def machine68k_mem_block_test(mem):
    # write bytes block
    data = b"hello, world!"
    mem.w_block(0, data)
    res = mem.r_block(0, len(data))
    assert res == data
    # clear block and read back
    mem.clear_block(0x200, 100, 42)
    res = mem.r_block(0x200, 100)
    assert res == bytes([42] * 100)
    # copy block and read back
    mem.copy_block(0x200, 0x300, 20)
    res = mem.r_block(0x300, 21)
    assert res == bytes([42] * 20) + b"\0"


def machine68k_mem_cstr_test(mem):
    data = "hello, world"
    mem.w_cstr(0, data)
    assert mem.r_cstr(0) == data
    empty = ""
    mem.w_cstr(100, empty)
    assert mem.r_cstr(100) == empty


def machine68k_mem_bstr_test(mem):
    data = "hello, world"
    mem.w_bstr(0, data)
    assert mem.r_bstr(0) == data
    empty = ""
    mem.w_bstr(100, empty)
    assert mem.r_bstr(100) == empty


class TraceAssert(object):
    def __init__(self, mem, mode, width, addr, value):
        self.mem = mem
        self.want = (mode, width, addr, value)

    def __enter__(self):
        self.mem.set_trace_mode(True)
        self.mem.set_trace_func(self.trace_func)
        self.match = None
        return self

    def __exit__(self, type, value, traceback):
        self.mem.set_trace_mode(False)
        self.mem.set_trace_func(None)
        assert self.match == self.want

    def trace_func(self, mode, width, addr, value):
        self.match = (mode, width, addr, value)


def machine68k_mem_trace_test(mem):
    with TraceAssert(mem, "R", 0, 0x100, 0):
        mem.cpu_r8(0x100)
    with TraceAssert(mem, "R", 1, 0x100, 0):
        mem.cpu_r16(0x100)
    with TraceAssert(mem, "R", 2, 0x100, 0):
        mem.cpu_r32(0x100)
    with TraceAssert(mem, "W", 0, 0x100, 0x42):
        mem.cpu_w8(0x100, 0x42)
    with TraceAssert(mem, "W", 1, 0x100, 0xDEAD):
        mem.cpu_w16(0x100, 0xDEAD)
    with TraceAssert(mem, "W", 2, 0x100, 0xCAFEBABE):
        mem.cpu_w32(0x100, 0xCAFEBABE)


def machine68k_mem_trace_error_test(mem):
    def trace_func(mode, width, addr, value):
        raise ValueError("bonk!")

    mem.set_trace_mode(True)
    mem.set_trace_func(trace_func)
    with pytest.raises(ValueError):
        mem.cpu_r8(0x100)
    with pytest.raises(ValueError):
        mem.cpu_w8(0x100, 0)
    mem.set_trace_mode(False)
    mem.set_trace_func(None)


def machine68k_mem_invalid_access_error_test(mem):
    def invalid_func(mode, width, addr):
        raise ValueError("bonk!")

    mem.set_invalid_func(invalid_func)
    with pytest.raises(ValueError):
        mem.cpu_r8(0x100000)
    with pytest.raises(ValueError):
        mem.cpu_w8(0x100000, 0)
    mem.set_invalid_func(None)


def machine68k_mem_special_rw_error_test(mem):
    def read(addr):
        raise ValueError("blonk!")

    def write(addr, val):
        raise ValueError("blonk!")

    mem.set_special_range_read_funcs(0xBF0000, 1, read, None, None)
    mem.set_special_range_write_funcs(0xBF0000, 1, write, None, None)
    with pytest.raises(ValueError):
        mem.cpu_r8(0xBF0000)
    with pytest.raises(ValueError):
        mem.cpu_w8(0xBF0000, 42)
