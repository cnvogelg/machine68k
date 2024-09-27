from machine68k import CPUType, Machine
from opcodes import op_reset


class Context:
    def __init__(self):
        self.m = Machine(CPUType.M68000, 1024)
        self.mem = self.m.mem
        self.cpu = self.m.cpu
        self.traps = self.m.traps

        self.mem.w32(0, 0x800)  # init sp
        self.mem.w32(4, 0x400)  # init pc
        # set supervisor stacks
        self.cpu.w_isp(0x700)
        self.cpu.w_msp(0x780)
        # trigger reset (read sp and init pc)
        self.cpu.pulse_reset()

        def end_func(opcode, pc):
            self.cpu.end()

        tid = self.traps.setup(end_func)
        self.opc_end = 0xA000 | tid
        self.code = 0x400

    def cleanup(self):
        self.m.cleanup()


def write_traps(ctx, num, addr, opc):
    ptr = addr
    for i in range(num):
        ctx.mem.w16(ptr, opc)
        ptr += 2
    ctx.mem.w16(ptr, ctx.opc_end)


def setup_run(ctx, total, func, **trap_args):
    count = 0

    def wrap(opcode, pc):
        nonlocal count
        count += 1
        func(opcode, pc)

    tid = ctx.traps.setup(wrap, **trap_args)
    opc = 0xA000 | tid

    write_traps(ctx, total, ctx.code, opc)

    def run():
        nonlocal count
        count = 0
        ctx.cpu.pulse_reset()
        er = ctx.cpu.execute(100_000)
        assert count == total
        assert er.cycles == (total + 1) * 4

    return run


def dummy_trap(opc, pc):
    pass


def fibo(n):
    if n in {0, 1}:
        return n
    return fibo(n - 1) + fibo(n - 2)


def fibo_trap(opc, pc):
    fibo(8)


def machine68k_machine_dummy_traps_benchmark(benchmark):
    c = Context()
    total = 10000

    benchmark(setup_run(c, total, dummy_trap))
    c.cleanup()


def machine68k_machine_dummy_traps_defer_benchmark(benchmark):
    c = Context()
    total = 10000

    benchmark(setup_run(c, total, dummy_trap, defer=True))
    c.cleanup()


def machine68k_machine_dummy_traps_defer_oldpc_benchmark(benchmark):
    c = Context()
    total = 10000

    benchmark(setup_run(c, total, dummy_trap, defer=True, old_pc=True))
    c.cleanup()


def machine68k_machine_fibo_traps_benchmark(benchmark):
    c = Context()
    total = 1000

    benchmark(setup_run(c, total, fibo_trap))
    c.cleanup()


def machine68k_machine_fibo_traps_defer_benchmark(benchmark):
    c = Context()
    total = 1000

    benchmark(setup_run(c, total, fibo_trap, defer=True))
    c.cleanup()


def machine68k_machine_fibo_traps_defer_oldpc_benchmark(benchmark):
    c = Context()
    total = 1000

    benchmark(setup_run(c, total, fibo_trap, defer=True, old_pc=True))
    c.cleanup()
