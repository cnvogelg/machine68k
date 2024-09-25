import pytest
from machine68k import Machine, CPUType
from opcodes import op_reset, op_jsr, op_rts


def setup_machine():
    m = Machine(CPUType.M68000, 1025)
    mem = m.mem
    cpu = m.cpu
    traps = m.traps
    mem.w32(0, 0x800)  # init sp
    mem.w32(4, 0x400)  # init pc
    # set supervisor stacks
    cpu.w_isp(0x700)
    cpu.w_msp(0x780)
    # trigger reset (read sp and init pc)
    cpu.pulse_reset()

    # end run (user flag) on reset opcode
    def my_end(opcode, pc):
        cpu.end()

    tid = traps.setup(my_end)
    opc = 0xA000 | tid
    return m, mem, cpu, traps, 0x400, opc


def gen_code(mem, code, opc):
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, opc)
    mem.w16(code + 8, op_rts)


def machine68k_machine_simple_reset_test():
    m, mem, cpu, traps, code, opc = setup_machine()
    mem.w16(code, opc)
    cycles = cpu.execute(2000)
    m.cleanup()
    assert cycles == 4


# ----- test cpu callback funcs -----


def machine68k_machine_pc_changed_func_test():
    m, mem, cpu, traps, code, opc = setup_machine()
    a = []

    def my_func(pc):
        a.append(pc)

    cpu.set_pc_changed_callback(my_func)
    gen_code(mem, code, opc)
    cpu.execute(2000)
    m.cleanup()
    assert a == [code + 8, code + 6]


def machine68k_machine_pc_changed_func_raise_test():
    m, mem, cpu, traps, code, opc = setup_machine()

    def my_func(pc):
        raise ValueError("foo")

    cpu.set_pc_changed_callback(my_func)
    gen_code(mem, code, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()


def machine68k_machine_reset_instr_test():
    m, mem, cpu, traps, code, opc = setup_machine()
    a = []

    def my_func():
        a.append(cpu.r_pc())

    cpu.set_reset_instr_callback(my_func)
    mem.w16(code, op_reset)
    mem.w16(code + 2, opc)
    cpu.execute(2000)
    m.cleanup()
    assert a == [code + 2]


def machine68k_machine_reset_instr_raise_test():
    m, mem, cpu, traps, code, opc = setup_machine()

    def my_func():
        raise ValueError("foo")

    cpu.set_reset_instr_callback(my_func)
    mem.w16(code, op_reset)
    mem.w16(code + 2, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()


def machine68k_machine_instr_func_test():
    m, mem, cpu, traps, code, opc = setup_machine()
    a = []

    def my_func(pc):
        a.append(pc)

    cpu.set_instr_hook_callback(my_func)
    gen_code(mem, code, opc)
    cpu.execute(2000)
    m.cleanup()
    assert a == [code, code + 8, code + 6]


def machine68k_machine_instr_func_raise_test():
    m, mem, cpu, traps, code, opc = setup_machine()

    def my_func(pc):
        raise ValueError("foo")

    cpu.set_instr_hook_callback(my_func)
    gen_code(mem, code, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()


# ----- traps -----


def machine68k_machine_trap_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)
    cycles = cpu.execute(2000)
    m.cleanup()
    assert a == [opc, code]
    assert cycles == 8


def machine68k_machine_trap_raise_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)
    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()


def machine68k_machine_trap_defer_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)
    cycles = cpu.execute(2000)
    m.cleanup()
    assert cycles == 8
    assert a == [opc, code]


def machine68k_machine_trap_defer_oldpc_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)
        assert cpu.r_pc() == pc

    tid = traps.setup(my_func, defer=True, old_pc=True)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)
    cycles = cpu.execute(2000)
    m.cleanup()
    assert cycles == 8
    assert a == [opc, code]


def machine68k_machine_trap_defer_raise_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)
    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()


def machine68k_machine_trap_autorts_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, auto_rts=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, opc_end)
    mem.w16(code + 8, opc)
    cycles = cpu.execute(2000)
    m.cleanup()
    assert a == [opc, code + 8]
    assert cycles == 28


def machine68k_machine_trap_autorts_raise_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func, auto_rts=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, opc_end)
    mem.w16(code + 8, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()


def machine68k_machine_trap_autorts_defer_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()
    a = []
    instr = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, auto_rts=True, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, opc_end)
    mem.w16(code + 8, opc)

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)
    cycles = cpu.execute(2000)
    m.cleanup()
    assert instr == [code, code + 8, code + 6]
    assert a == [opc, code + 8]
    assert cycles == 28


def machine68k_machine_trap_autorts_defer_raise_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func, auto_rts=True, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, opc_end)
    mem.w16(code + 8, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()


# ----- execute nesting -----


def machine68k_machine_recurse_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        cycles = cpu.execute(1000)
        assert cycles == 10
        cpu.w_pc(pc)

    tid = traps.setup(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)
    mem.w16(code + 10, opc_end)
    # recursively called execute is not allowed in regular trap
    with pytest.raises(RuntimeError):
        cpu.execute(2000)
    m.cleanup()


def machine68k_machine_recurse_defer_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        cycles = cpu.execute(1000)
        assert cycles == 4
        cpu.w_pc(pc)

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)
    mem.w16(code + 10, opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)

    cycles = cpu.execute(2000)
    m.cleanup()
    assert cycles == 8
    assert instr == [code, code + 10, code + 2]


def machine68k_machine_recurse_twice_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()
    a = []

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        cpu.execute(1000)
        cpu.w_pc(pc)

    def my_func2(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid

    tid2 = traps.setup(my_func2, defer=True)
    opc2 = 0xA000 | tid2

    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)

    mem.w16(code + 10, opc2)
    mem.w16(code + 12, opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)

    cpu.execute(2000)
    m.cleanup()
    assert instr == [code, code + 10, code + 12, code + 2]
    assert a == [opc2, code + 10]


def machine68k_machine_recurse_twice_raise_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        cpu.execute(1000)
        cpu.w_pc(pc)

    def my_func2(opcode, pc):
        raise ValueError("foo")

    tid = traps.setup(my_func, defer=True)
    opc = 0xA000 | tid

    tid2 = traps.setup(my_func2, defer=True)
    opc2 = 0xA000 | tid2

    mem.w16(code, opc)
    mem.w16(code + 2, opc_end)

    mem.w16(code + 10, opc2)
    mem.w16(code + 12, opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)

    with pytest.raises(ValueError):
        cpu.execute(2000)
    m.cleanup()
    assert instr == [code, code + 10]
