import pytest
from machine68k import (
    Machine,
    CPU,
    Register,
    CPUType,
    cpu_type_from_str,
    cpu_type_to_str,
)


@pytest.fixture(params=["cpu", "local", "remote"])
def cpu(request):
    mode = request.param
    if mode == "cpu":
        yield CPU(CPUType.M68000)
    elif mode == "local":
        m = Machine(CPUType.M68000, 16)
        yield m.cpu
        m.cleanup()
    else:
        rmachine68k = pytest.importorskip("rmachine68k")
        client = request.getfixturevalue("remote_client")
        m = rmachine68k.create_machine(client, "68000", 16)
        yield m.cpu


def machine68k_cpu_type_test():
    assert cpu_type_from_str("M68000") == CPUType.M68000
    assert cpu_type_from_str("68000") == CPUType.M68000
    assert cpu_type_from_str("00") == CPUType.M68000
    # invalid name
    with pytest.raises(ValueError):
        cpu_type_from_str("bla")
    assert cpu_type_to_str(CPUType.M68000) == "68000"
    assert cpu_type_to_str(CPUType.M68020) == "68020"
    assert cpu_type_to_str("bla") is None


def machine68k_cpu_type_test(cpu_type):
    cpu = CPU(cpu_type)
    assert cpu.get_cpu_type() == cpu_type
    cpu_name = cpu_type_to_str(cpu_type)
    assert cpu.get_cpu_name() == cpu_name
    assert repr(cpu) == f"CPU(type={cpu_name})"


def machine68k_cpu_rw_reg_test(cpu):
    cpu.w_reg(Register.D0, 0xDEADBEEF)
    assert cpu.r_reg(Register.D0) == 0xDEADBEEF
    # invalid values
    with pytest.raises(OverflowError):
        cpu.w_reg(Register.D0, 0xDEADBEEF12)
    with pytest.raises(OverflowError):
        cpu.w_reg(Register.D0, -1)
    with pytest.raises(TypeError):
        cpu.w_reg(Register.D0, "hello")


def machine68k_cpu_rws_reg_test(cpu):
    cpu.ws_reg(Register.D0, -123)
    assert cpu.rs_reg(Register.D0) == -123
    # invalid values
    with pytest.raises(OverflowError):
        cpu.ws_reg(Register.D0, 0x80000000)
    with pytest.raises(OverflowError):
        cpu.ws_reg(Register.D0, -0x80000001)
    with pytest.raises(TypeError):
        cpu.ws_reg(Register.D0, "hello")


def machine68k_cpu_rw_partial_reg_test(cpu):
    cpu.w_reg(Register.D0, 0xCAFEBABE)
    # read partial
    assert cpu.r32_reg(Register.D0) == 0xCAFEBABE
    assert cpu.r16_reg(Register.D0) == 0xBABE
    assert cpu.r8_reg(Register.D0) == 0xBE
    # write partial
    cpu.w8_reg(Register.D0, 0xFE)
    assert cpu.r_reg(Register.D0) == 0xCAFEBAFE
    cpu.w16_reg(Register.D0, 0xF000)
    assert cpu.r_reg(Register.D0) == 0xCAFEF000
    cpu.w32_reg(Register.D0, 0xDEADBEEF)
    assert cpu.r_reg(Register.D0) == 0xDEADBEEF
    # write too large
    with pytest.raises(OverflowError):
        cpu.w8_reg(Register.D0, 0xF00)
    with pytest.raises(OverflowError):
        cpu.w16_reg(Register.D0, 0xF0000)
    with pytest.raises(OverflowError):
        cpu.w32_reg(Register.D0, 0xF00000000)


def machine68k_cpu_rws_partial_reg_test(cpu):
    cpu.w_reg(Register.D0, 0xF000F0F0)
    # read partial
    assert cpu.r32s_reg(Register.D0) == -268373776
    assert cpu.r16s_reg(Register.D0) == -3856
    assert cpu.r8s_reg(Register.D0) == -16
    # write partial
    cpu.w8s_reg(Register.D0, -1)
    assert cpu.r_reg(Register.D0) == 0xF000F0FF
    cpu.w16s_reg(Register.D0, -1)
    assert cpu.r_reg(Register.D0) == 0xF000FFFF
    cpu.w32s_reg(Register.D0, -1)
    assert cpu.r_reg(Register.D0) == 0xFFFFFFFF
    # write too large
    with pytest.raises(OverflowError):
        cpu.w8s_reg(Register.D0, 0x80)
    with pytest.raises(OverflowError):
        cpu.w16s_reg(Register.D0, 0x8000)
    with pytest.raises(OverflowError):
        cpu.w32s_reg(Register.D0, 0x80000000)


def machine68k_cpu_rw_context_test(cpu):
    ctx = cpu.get_cpu_context()
    cpu.set_cpu_context(ctx)
