import pytest
from machine68k import Machine, CPUType
from opcodes import op_reset, op_jsr, op_rts


def setup_machine():
    m = Machine(CPUType.M68000, 1025)
    mem = m.mem
    cpu = m.cpu
    mem.w32(0, 0x800)  # init sp
    mem.w32(4, 0x400)  # init pc
    # set supervisor stacks
    cpu.w_isp(0x700)
    cpu.w_msp(0x780)
    # trigger reset (read sp and init pc)
    cpu.pulse_reset()

    # end run (user flag) on reset opcode
    def my_end():
        cpu.end()

    cpu.set_reset_instr_callback(my_end)
    return m, mem, cpu, 0x400


def gen_code(mem, code):
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, op_reset)
    mem.w16(code + 8, op_rts)


def machine68k_machine_simple_reset_test():
    m, mem, cpu, code = setup_machine()
    mem.w16(code, op_reset)
    cycles = cpu.execute(2000)
    assert cycles == 132


# ----- test cpu callback funcs -----


def machine68k_machine_pc_changed_func_test():
    m, mem, cpu, code = setup_machine()
    a = []

    def my_func(pc):
        a.append(pc)

    cpu.set_pc_changed_callback(my_func)
    gen_code(mem, code)
    cpu.execute(2000)
    assert a == [code + 8, code + 6]


def machine68k_machine_pc_changed_func_raise_test():
    m, mem, cpu, code = setup_machine()

    def my_func(pc):
        raise ValueError("foo")

    cpu.set_pc_changed_callback(my_func)
    gen_code(mem, code)
    with pytest.raises(ValueError):
        cpu.execute(2000)


def machine68k_machine_reset_instr_raise_test():
    m, mem, cpu, code = setup_machine()

    def my_func():
        raise ValueError("foo")

    cpu.set_reset_instr_callback(my_func)
    gen_code(mem, code)
    with pytest.raises(ValueError):
        cpu.execute(2000)


def machine68k_machine_instr_func_test():
    m, mem, cpu, code = setup_machine()
    a = []

    def my_func(pc):
        a.append(pc)

    cpu.set_instr_hook_callback(my_func)
    gen_code(mem, code)
    cpu.execute(2000)
    assert a == [code, code + 8, code + 6]


def machine68k_machine_instr_func_raise_test():
    m, mem, cpu, code = setup_machine()

    def my_func(pc):
        raise ValueError("foo")

    cpu.set_instr_hook_callback(my_func)
    gen_code(mem, code)
    with pytest.raises(ValueError):
        cpu.execute(2000)


# ----- traps -----


def machine68k_machine_trap_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, op_reset)
    cpu.execute(2000)
    assert a == [opc, code]


def machine68k_machine_trap_raise_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, op_reset)
    with pytest.raises(ValueError):
        cpu.execute(2000)


def machine68k_machine_trap_defer_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, op_reset)
    cpu.execute(2000)
    assert a == [opc, code]


def machine68k_machine_trap_defer_raise_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, op_reset)
    with pytest.raises(ValueError):
        cpu.execute(2000)


def machine68k_machine_trap_autorts_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, auto_rts=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, op_reset)
    mem.w16(code + 8, opc)
    cpu.execute(2000)
    assert a == [opc, code + 8]


def machine68k_machine_trap_autorts_raise_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func, auto_rts=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, op_reset)
    mem.w16(code + 8, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)


def machine68k_machine_trap_autorts_defer_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps
    a = []
    instr = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, auto_rts=True, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, op_reset)
    mem.w16(code + 8, opc)

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)
    cpu.execute(2000)
    assert instr == [code, code + 8, code + 6]
    assert a == [opc, code + 8]


def machine68k_machine_trap_autorts_defer_raise_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func, auto_rts=True, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, op_reset)
    mem.w16(code + 8, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)


# ----- execute nesting -----


def machine68k_machine_recurse_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        cycles = cpu.execute(1000)
        assert cycles == 10
        cpu.w_pc(pc)

    tid = traps.setup(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, op_reset)
    mem.w16(code + 10, op_reset)
    # recursively called execute is not allowed in regular trap
    with pytest.raises(RuntimeError):
        cpu.execute(2000)


def machine68k_machine_recurse_defer_test():
    m, mem, cpu, code = setup_machine()
    traps = m.traps

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        cpu.execute(1000)
        cpu.w_pc(pc)

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, op_reset)
    mem.w16(code + 10, op_reset)

    instr = []

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)

    # recursively called execute is not allowed in regular trap
    cpu.execute(2000)
    assert instr == [code, code + 10, code + 2]
