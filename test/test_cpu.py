import pytest
from machine68k import CPU, Register, CPUType


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
