import pytest
from machine68k import Machine, CPUType
from opcodes import op_reset, op_jsr, op_rts, op_jmp

ended = False


@pytest.fixture(params=["local", "remote"])
def setup_machine(request):
    mode = request.param
    if mode == "remote":
        m = request.getfixturevalue("remote_machine")
    else:
        m = Machine(CPUType.M68000, 1024)
        assert repr(m) == "Machine(CPU(type=68000),Memory(ram_size_kib=1024))"
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
        global ended
        ended = True

    tid = traps.alloc(my_end)
    opc = 0xA000 | tid
    return m, mem, cpu, traps, 0x400, opc


def gen_code(mem, code, opc):
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, opc)
    mem.w16(code + 8, op_rts)


def machine68k_machine_simple_run_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine
    mem.w16(code, opc)
    global ended
    ended = False
    er = cpu.execute(2000)
    assert er.was_trap
    traps.call()
    assert ended
    assert er.cycles == 4


def machine68k_machine_run_dual_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine
    mem.w16(code, opc)
    # first run
    er = cpu.execute(2000)
    assert er.cycles == 4
    # second run
    cpu.w_pc(code)
    er = cpu.execute(2000)
    assert er.cycles == 4


def machine68k_machine_max_cycles_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine
    # endless loop
    mem.w16(code, op_jmp)
    mem.w32(code + 2, code)
    # exact cycles
    er = cpu.execute(40)
    assert er.cycles == 40
    # too few
    er = cpu.execute(10)
    assert er.cycles == 12


# ----- test cpu callback funcs -----


def machine68k_machine_pc_changed_func_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine
    a = []

    def my_func(pc):
        a.append(pc)

    cpu.set_pc_changed_callback(my_func)
    gen_code(mem, code, opc)
    cpu.execute(2000)
    assert a == [code + 8, code + 6]


def machine68k_machine_pc_changed_func_raise_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine

    def my_func(pc):
        raise ValueError("foo")

    cpu.set_pc_changed_callback(my_func)
    gen_code(mem, code, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)


def machine68k_machine_reset_instr_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine
    a = []

    def my_func():
        a.append(cpu.r_pc())

    cpu.set_reset_instr_callback(my_func)
    mem.w16(code, op_reset)
    mem.w16(code + 2, opc)
    cpu.execute(2000)
    assert a == [code + 2]


def machine68k_machine_reset_instr_raise_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine

    def my_func():
        raise ValueError("foo")

    cpu.set_reset_instr_callback(my_func)
    mem.w16(code, op_reset)
    mem.w16(code + 2, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)


def machine68k_machine_instr_func_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine
    a = []

    def my_func(pc):
        a.append(pc)

    cpu.set_instr_hook_callback(my_func)
    gen_code(mem, code, opc)
    cpu.execute(2000)
    assert a == [code, code + 8, code + 6]


def machine68k_machine_instr_func_raise_test(setup_machine):
    m, mem, cpu, traps, code, opc = setup_machine

    def my_func(pc):
        raise ValueError("foo")

    cpu.set_instr_hook_callback(my_func)
    gen_code(mem, code, opc)
    with pytest.raises(ValueError):
        cpu.execute(2000)


# ----- traps -----


def machine68k_machine_trap_test(setup_machine):
    m, mem, cpu, traps, code, opc_end = setup_machine
    a = []

    def my_func(opcode, pc):
        # in a normal trap the current trap is not accounted, yet
        a.append(opcode)
        a.append(pc)

    tid = traps.alloc(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    er = cpu.execute(2000)
    assert er.was_trap
    traps.call()
    assert a == [opc, code]
    assert er.cycles == 4


def machine68k_machine_trap_raise_test(setup_machine):
    m, mem, cpu, traps, code, opc_end = setup_machine

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = traps.alloc(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    er = cpu.execute(2000)
    assert er.was_trap
    with pytest.raises(ValueError):
        traps.call()


# ----- execute nesting -----


def machine68k_machine_recurse_test(setup_machine):
    m, mem, cpu, traps, code, opc_end = setup_machine

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        er = cpu.execute(1000)
        assert er.cycles == 4
        assert er.was_trap
        traps.call()
        cpu.w_pc(pc)

    tid = traps.alloc(my_func)
    opc = 0xA000 | tid
    mem.w16(code, opc)
    mem.w16(code + 10, opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)

    er = cpu.execute(2000)
    assert er.was_trap
    assert er.cycles == 4
    traps.call()
    assert instr == [code, code + 10]


def machine68k_machine_recurse_twice_test(setup_machine):
    m, mem, cpu, traps, code, opc_end = setup_machine
    a = []

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        er = cpu.execute(1000)
        cpu.w_pc(pc)
        assert er.cycles == 4
        assert er.was_trap
        traps.call()

    def my_func2(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.alloc(my_func)
    opc = 0xA000 | tid

    tid2 = traps.alloc(my_func2)
    opc2 = 0xA000 | tid2

    mem.w16(code, opc)

    mem.w16(code + 10, opc2)

    instr = []

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)

    er = cpu.execute(2000)
    assert er.cycles == 4
    assert er.was_trap
    traps.call()
    assert instr == [code, code + 10]
    assert a == [opc2, code + 10]


def machine68k_machine_recurse_twice_raise_test(setup_machine):
    m, mem, cpu, traps, code, opc_end = setup_machine

    def my_func(opcode, pc):
        pc = cpu.r_pc()
        cpu.w_pc(code + 10)
        er = cpu.execute(1000)
        assert er.was_trap
        # this will raise the value error
        traps.call()
        cpu.w_pc(pc)

    def my_func2(opcode, pc):
        raise ValueError("foo")

    tid = traps.alloc(my_func)
    opc = 0xA000 | tid

    tid2 = traps.alloc(my_func2)
    opc2 = 0xA000 | tid2

    mem.w16(code, opc)

    mem.w16(code + 10, opc2)

    instr = []

    def out(pc):
        instr.append(pc)

    cpu.set_instr_hook_callback(out)

    er = cpu.execute(2000)
    assert er.was_trap
    with pytest.raises(ValueError):
        traps.call()
    assert instr == [code, code + 10]
