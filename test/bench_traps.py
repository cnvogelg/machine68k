from machine68k import CPUType, Machine
from opcodes import op_reset


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

    def end_func(opcode, pc):
        cpu.end()

    tid = traps.setup(end_func)
    opc_end = 0xA000 | tid
    return m, mem, cpu, traps, 0x400, opc_end


def write_traps(mem, code, opc, num, opc_end):
    ptr = code
    for i in range(num):
        mem.w16(ptr, opc)
        ptr += 2
    mem.w16(ptr, opc_end)


def machine68k_machine_traps_benchmark(benchmark):
    m, mem, cpu, traps, code, opc_end = setup_machine()

    total = 10000
    count = 0

    def dummy(opc, pc):
        nonlocal count
        count += 1

    tid = traps.setup(dummy)
    opc = 0xA000 | tid

    write_traps(mem, code, opc, total, opc_end)

    def run():
        nonlocal count
        count = 0
        cpu.pulse_reset()
        cycles = cpu.execute(100_000)
        assert count == total
        assert cycles == (total + 1) * 4

    benchmark(run)
    m.cleanup()


def machine68k_machine_defer_traps_benchmark(benchmark):
    m, mem, cpu, traps, code, opc_end = setup_machine()

    total = 10000
    count = 0

    def dummy(opc, pc):
        nonlocal count
        count += 1

    tid = traps.setup(dummy, defer=True)
    opc = 0xA000 | tid

    write_traps(mem, code, opc, total, opc_end)

    def run():
        nonlocal count
        count = 0
        cpu.pulse_reset()
        cycles = cpu.execute(100_000)
        assert count == total
        assert cycles == (total + 1) * 4

    benchmark(run)
    m.cleanup()
