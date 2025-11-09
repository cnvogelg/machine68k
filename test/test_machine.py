import pytest
from machine68k import Machine, CPUType
from opcodes import op_reset, op_jsr, op_rts, op_jmp, op_nop


class Context:
    def __init__(self, mach, mode):
        self.mach = mach
        self.mode = mode
        self.mem = self.mach.mem
        self.cpu = self.mach.cpu
        self.traps = self.mach.traps

        self.mem.w32(0, 0x600)  # init sp
        self.mem.w32(4, 0x800)  # init pc
        # trigger reset (read sp and init pc)
        reset_cycles = self.cpu.pulse_reset()
        self.cpu.execute(reset_cycles)

        self.end_obj = self.mach.create_execute_end("exit")

        def end_func(opcode, pc):
            return self.end_obj

        self.tid = self.traps.alloc(end_func)
        self.opc_end = 0xA000 | self.tid

        self.code = 0x800
        self.end_addr = 0x400
        self.mem.w16(self.end_addr, self.opc_end)

        # write end trap to stack
        sp = self.cpu.r_sp()
        self.mem.w32(sp, self.end_addr)

    def cleanup(self):
        self.traps.free(self.tid)
        self.mach.cleanup()


@pytest.fixture(params=["local", "remote"])
def ctx(request):
    mode = request.param
    if mode == "remote":
        m = request.getfixturevalue("remote_machine")
    else:
        m = Machine(CPUType.M68000, 1024)
        assert repr(m) == "Machine(CPU(type=68000),Memory(ram_size_kib=1024))"
    return Context(m, mode)


def gen_code(ctx, opc):
    ctx.mem.w16(ctx.code, op_jsr)
    ctx.mem.w32(ctx.code + 2, ctx.code + 8)
    ctx.mem.w16(ctx.code + 6, opc)
    ctx.mem.w16(ctx.code + 8, op_rts)


# --- execute()


def machine68k_machine_execute_rts_test(ctx):
    # run a single rts and exit via end trap
    ctx.mem.w16(ctx.code, op_rts)
    er = ctx.mach.execute(1000)
    assert er.result is ctx.end_obj
    assert er.cycles == 20
    assert er.sum_cycles == 20


def machine68k_machine_execute_max_cycles_test(ctx):
    # run a single rts and exit via end trap
    # fill nops
    ptr = ctx.code
    for i in range(1000):
        ctx.mem.w16(ptr, op_nop)
        ptr += 2
    # run and return after cycles
    er = ctx.mach.execute(100)
    assert er.result is None
    assert er.cycles == 100
    assert er.sum_cycles == 100
    # run too few
    er = ctx.mach.execute(2)
    assert er.result is None
    assert er.cycles == 4
    assert er.sum_cycles == 4


def machine68k_machine_execute_max_cycles_test(ctx):
    # endless loop
    ctx.mem.w16(ctx.code, op_jmp)
    ctx.mem.w32(ctx.code + 2, ctx.code)
    # exact cycles
    er = ctx.mach.execute(40)
    assert er.result is None
    assert er.cycles == 48
    assert er.sum_cycles == 48
    # too few
    er = ctx.mach.execute(10)
    assert er.cycles == 12
    assert er.sum_cycles == 12


# ----- test cpu callback funcs -----


def machine68k_machine_pc_changed_func_test(ctx):
    a = []

    def my_func(pc):
        a.append(pc)

    ctx.cpu.set_pc_changed_callback(my_func)
    gen_code(ctx, op_nop)
    er = ctx.mach.execute(2000)
    assert er.result is ctx.end_obj
    assert er.cycles == 60
    assert er.sum_cycles == 60
    assert a == [ctx.code + 8, ctx.code + 6, ctx.end_addr]


def machine68k_machine_pc_changed_func_raise_test(ctx):

    def my_func(pc):
        raise ValueError("foo")

    ctx.cpu.set_pc_changed_callback(my_func)
    gen_code(ctx, op_nop)
    with pytest.raises(ValueError):
        ctx.mach.execute(2000)


def machine68k_machine_reset_instr_test(ctx):
    a = []

    def my_func():
        a.append(ctx.cpu.r_pc())

    ctx.cpu.set_reset_instr_callback(my_func)
    ctx.mem.w16(ctx.code, op_reset)
    ctx.mem.w16(ctx.code + 2, op_rts)
    er = ctx.mach.execute(2000)
    assert er.result is ctx.end_obj
    assert a == [ctx.code + 2]


def machine68k_machine_reset_instr_raise_test(ctx):

    def my_func():
        raise ValueError("foo")

    ctx.cpu.set_reset_instr_callback(my_func)
    ctx.mem.w16(ctx.code, op_reset)
    ctx.mem.w16(ctx.code + 2, op_rts)
    with pytest.raises(ValueError):
        ctx.mach.execute(2000)


def machine68k_machine_instr_func_test(ctx):
    a = []

    def my_func(pc):
        a.append(pc)

    ctx.cpu.set_instr_hook_callback(my_func)
    gen_code(ctx, op_nop)
    ctx.mach.execute(2000)
    assert a == [ctx.code, ctx.code + 8, ctx.code + 6, ctx.code + 8, ctx.end_addr]


def machine68k_machine_instr_func_raise_test(ctx):

    def my_func(pc):
        raise ValueError("foo")

    ctx.cpu.set_instr_hook_callback(my_func)
    gen_code(ctx, op_nop)
    with pytest.raises(ValueError):
        ctx.mach.execute(2000)


# ----- traps -----


def machine68k_machine_trap_simple_test(ctx):
    """call a simple trap"""
    a = []

    def my_func(opcode, pc):
        # in a normal trap the current trap is not accounted, yet
        a.append(opcode)
        a.append(pc)
        # fetch the current state
        state = ctx.mach.get_state()
        assert state.cycles == 4
        assert state.sum_cycles == 4
        assert state.result is None

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid
    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, op_rts)
    er = ctx.mach.execute(2000)
    assert a == [opc, ctx.code]
    assert er.result is ctx.end_obj
    assert er.cycles == 24
    assert er.sum_cycles == 24
    ctx.traps.free(tid)


def machine68k_machine_trap_end_test(ctx):
    """call a trap that ends the execution"""
    a = []
    # create an own trap end
    my_end_obj = ctx.mach.create_execute_end("my_end")

    def my_func(opcode, pc):
        # in a normal trap the current trap is not accounted, yet
        a.append(opcode)
        a.append(pc)
        return my_end_obj

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid
    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, op_rts)
    er = ctx.mach.execute(2000)
    assert a == [opc, ctx.code]
    assert er.result is my_end_obj
    assert er.cycles == 4
    assert er.sum_cycles == 4
    ctx.traps.free(tid)


def machine68k_machine_trap_abort_test(ctx):
    """call abort inside a trap to end the execution"""
    a = []

    def my_func(opcode, pc):
        # in a normal trap the current trap is not accounted, yet
        a.append(opcode)
        a.append(pc)
        # call abort with default abort object
        ctx.mach.abort_execute()

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid
    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, op_rts)
    er = ctx.mach.execute(2000)
    assert a == [opc, ctx.code]
    # return special abort res object
    assert er.result is ctx.mach.get_abort_default()
    assert er.cycles == 4
    assert er.sum_cycles == 4
    ctx.traps.free(tid)


def machine68k_machine_trap_abort_custom_test(ctx):
    """call abort inside a trap to end the execution"""
    a = []

    custom_abort = ctx.mach.create_execute_end("custom_abort")

    def my_func(opcode, pc):
        # in a normal trap the current trap is not accounted, yet
        a.append(opcode)
        a.append(pc)
        # call abort with custom abort object
        ctx.mach.abort_execute(custom_abort)

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid
    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, op_rts)
    er = ctx.mach.execute(2000)
    assert a == [opc, ctx.code]
    # return my abort res object
    assert er.result is custom_abort
    assert er.cycles == 4
    assert er.sum_cycles == 4
    ctx.traps.free(tid)


def machine68k_machine_trap_raise_test(ctx):
    """raise an exception in a trap"""

    def my_func(opcode, pc):
        raise ValueError("foo")

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid
    ctx.mem.w16(ctx.code, opc)
    with pytest.raises(ValueError) as excinfo:
        ctx.mach.execute(2000)

    # in local run expect the location to be my_func
    if ctx.mode == "local":
        frame = excinfo.traceback[-1]
        assert frame.name == "my_func"

    ctx.traps.free(tid)


# ----- execute nesting -----


def machine68k_machine_recurse_test(ctx):
    """nest an execute call inside a trap"""

    def my_func(opcode, pc):
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 4
        # new pc
        pc = ctx.cpu.r_pc()
        ctx.cpu.w_pc(ctx.code + 10)
        # run new pc
        er = ctx.mach.execute(1000)
        assert er.cycles == 4
        assert er.sum_cycles == 8
        assert er.result == ctx.end_obj
        # restore pc
        ctx.cpu.w_pc(pc)
        # check state again
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 8

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid
    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, ctx.opc_end)
    ctx.mem.w16(ctx.code + 10, ctx.opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    ctx.cpu.set_instr_hook_callback(out)

    er = ctx.mach.execute(2000)
    assert er.result is ctx.end_obj
    assert er.cycles == 8
    assert er.sum_cycles == 12
    assert instr == [ctx.code, ctx.code + 10, ctx.code + 2]
    ctx.traps.free(tid)


def machine68k_machine_recurse_two_trap_test(ctx):
    """run code with trap and inside trap run another code with a trap"""
    a = []

    def my_func(opcode, pc):
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 4
        # set new pc
        pc = ctx.cpu.r_pc()
        ctx.cpu.w_pc(ctx.code + 10)
        # second run
        er = ctx.mach.execute(1000)
        assert er.result is ctx.end_obj
        assert er.cycles == 8
        assert er.sum_cycles == 12
        # restore pc
        ctx.cpu.w_pc(pc)
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 12

    def my_func2(opcode, pc):
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 8
        # store opcode and pc
        a.append(opcode)
        a.append(pc)

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid

    tid2 = ctx.traps.alloc(my_func2)
    opc2 = 0xA000 | tid2

    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, ctx.opc_end)

    ctx.mem.w16(ctx.code + 10, opc2)
    ctx.mem.w16(ctx.code + 12, ctx.opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    ctx.cpu.set_instr_hook_callback(out)

    er = ctx.mach.execute(2000)
    assert er.cycles == 8
    assert er.sum_cycles == 16
    assert er.result is ctx.end_obj

    assert instr == [ctx.code, ctx.code + 10, ctx.code + 12, ctx.code + 2]
    assert a == [opc2, ctx.code + 10]
    ctx.traps.free(tid)
    ctx.traps.free(tid2)


def machine68k_machine_recurse_two_trap_raise_test(ctx):
    """raise an exception in nested trap and let it fall through"""

    def my_func(opcode, pc):
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 4
        # new pc
        ctx.cpu.w_pc(ctx.code + 10)
        # sub run - will raise in my_func2
        ctx.mach.execute(1000)
        # never reach this
        raise RuntimeError("never be here!")

    def my_func2(opcode, pc):
        raise ValueError("foo")

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid

    tid2 = ctx.traps.alloc(my_func2)
    opc2 = 0xA000 | tid2

    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, ctx.opc_end)

    ctx.mem.w16(ctx.code + 10, opc2)
    ctx.mem.w16(ctx.code + 12, ctx.opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    ctx.cpu.set_instr_hook_callback(out)

    with pytest.raises(ValueError):
        ctx.mach.execute(2000)

    assert instr == [ctx.code, ctx.code + 10]
    ctx.traps.free(tid)
    ctx.traps.free(tid2)


def machine68k_machine_recurse_two_trap_except_test(ctx):
    """raise an exception and catch it inside run"""

    def my_func(opcode, pc):
        assert ctx.mach.get_nesting_level() == 1
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 4
        # new pc
        pc = ctx.cpu.r_pc()
        ctx.cpu.w_pc(ctx.code + 10)
        # sub run - will raise in my_func2
        with pytest.raises(ValueError):
            ctx.mach.execute(1000)
        # restore pc
        ctx.cpu.w_pc(pc)
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 8  # sub trap
        assert ctx.mach.get_nesting_level() == 1

    def my_func2(opcode, pc):
        assert ctx.mach.get_nesting_level() == 2
        # check current state
        state = ctx.mach.get_state()
        assert state.result is None
        assert state.cycles == 4
        assert state.sum_cycles == 8
        # now raise the error in the second run
        raise ValueError("foo")

    tid = ctx.traps.alloc(my_func)
    opc = 0xA000 | tid

    tid2 = ctx.traps.alloc(my_func2)
    opc2 = 0xA000 | tid2

    ctx.mem.w16(ctx.code, opc)
    ctx.mem.w16(ctx.code + 2, ctx.opc_end)

    ctx.mem.w16(ctx.code + 10, opc2)
    ctx.mem.w16(ctx.code + 12, ctx.opc_end)

    instr = []

    def out(pc):
        instr.append(pc)

    ctx.cpu.set_instr_hook_callback(out)

    assert ctx.mach.get_nesting_level() == 0
    er = ctx.mach.execute(2000)
    assert ctx.mach.get_nesting_level() == 0
    assert er.result is ctx.end_obj
    assert er.cycles == 8
    assert er.sum_cycles == 12

    assert instr == [ctx.code, ctx.code + 10, ctx.code + 2]
    ctx.traps.free(tid)
    ctx.traps.free(tid2)
