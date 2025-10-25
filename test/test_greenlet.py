import pytest
from machine68k import Machine, CPUType
from opcodes import op_reset, op_jsr, op_rts, op_jmp

greenlet = pytest.importorskip("greenlet")

ended = False


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
        global ended
        ended = True

    tid = traps.alloc(my_end)
    opc = 0xA000 | tid
    return m, mem, cpu, traps, 0x400, opc


def gen_code(mem, code, opc_end, opc_switch):
    mem.w16(code, op_jsr)
    mem.w32(code + 2, code + 8)
    mem.w16(code + 6, opc_end)
    mem.w16(code + 8, opc_switch)
    mem.w16(code + 10, op_rts)


def machine68k_switch_run_test():
    m, mem, cpu, traps, code, opc_end = setup_machine()

    run1_result = []
    run2_result = []

    def switch1(opcode, pc):
        ctx = cpu.get_cpu_context()
        glet2.switch()
        cpu.set_cpu_context(ctx)

    def switch2(opcode, pc):
        ctx = cpu.get_cpu_context()
        glet1.switch()
        cpu.set_cpu_context(ctx)

    tid1 = traps.alloc(switch1)
    opc1 = 0xA000 | tid1

    tid2 = traps.alloc(switch2)
    opc2 = 0xA000 | tid2

    def run1():
        cpu.w_pc(code)
        cpu.w_sp(0x700)
        global ended
        while not ended:
            er = cpu.execute(2000)
            if er.was_trap:
                traps.call()
        run1_result.append(er)
        # final switch to end run2
        glet2.switch()

    def run2():
        cpu.w_pc(code + 20)
        cpu.w_sp(0x600)
        global ended
        while not ended:
            er = cpu.execute(2000)
            if er.was_trap:
                traps.call()
        run2_result.append(er)

    # code1
    gen_code(mem, code, opc_end, opc1)

    # code2
    gen_code(mem, code + 20, opc_end, opc2)

    glet1 = greenlet.greenlet(run1)
    glet2 = greenlet.greenlet(run2)

    # start run1
    glet1.switch()

    assert len(run1_result) == 1
    assert len(run2_result) == 1

    m.cleanup()
