import pytest
from machine68k import CPU, Register, CPUType, cpu_type_from_str, cpu_type_to_str


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


def machine68k_cpu_rw_reg_test():
    cpu = CPU(CPUType.M68000)
    cpu.w_reg(Register.D0, 0xDEADBEEF)
    assert cpu.r_reg(Register.D0) == 0xDEADBEEF
    # invalid values
    with pytest.raises(OverflowError):
        cpu.w_reg(Register.D0, 0xDEADBEEF12)
    with pytest.raises(OverflowError):
        cpu.w_reg(Register.D0, -1)
    with pytest.raises(TypeError):
        cpu.w_reg(Register.D0, "hello")


def machine68k_cpu_rws_reg_test():
    cpu = CPU(CPUType.M68000)
    assert cpu.cpu_type == CPUType.M68000
    cpu.ws_reg(Register.D0, -123)
    assert cpu.rs_reg(Register.D0) == -123
    # invalid values
    with pytest.raises(OverflowError):
        cpu.ws_reg(Register.D0, 0x80000000)
    with pytest.raises(OverflowError):
        cpu.ws_reg(Register.D0, -0x80000001)
    with pytest.raises(TypeError):
        cpu.ws_reg(Register.D0, "hello")


def machine68k_cpu_rw_context_test():
    cpu = CPU(CPUType.M68000)
    ctx = cpu.get_cpu_context()
    cpu.set_cpu_context(ctx)
