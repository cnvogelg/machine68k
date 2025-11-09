from machine68k import CPUType, Machine
from opcodes import op_rts


class Context:
    def __init__(self):
        self.mach = Machine(CPUType.M68000, 1024)
        self.mem = self.mach.mem
        self.cpu = self.mach.cpu
        self.traps = self.mach.traps
        self.ended = False
        self.count = 0

        self.mem.w32(0, 0x600)  # init sp
        self.mem.w32(4, 0x800)  # init pc
        # trigger reset (read sp and init pc)
        self.cpu.pulse_reset()

        self.end_obj = self.mach.create_execute_end("exit")

        def end_func(opcode, pc):
            return self.end_obj

        self.tid = self.traps.alloc(end_func)
        self.opc_end = 0xA000 | self.tid

        # write end trap to stack
        sp = self.cpu.r_sp()
        self.mem.w32(sp, 0x400)
        self.mem.w16(0x400, self.opc_end)

        self.code = 0x800

    def cleanup(self):
        self.traps.free(self.tid)
        self.mach.cleanup()

    def has_ended(self):
        return self.ended


def setup_run(ctx, total):
    ctx.count = 0

    def trap_code(opcode, pc):
        ctx.count += 1

    tid = ctx.traps.alloc(trap_code)
    opc = 0xA000 | tid

    # write traps
    ptr = ctx.code
    for i in range(total):
        ctx.mem.w16(ptr, opc)
        ptr += 2

    # close with rts
    ctx.mem.w16(ptr, op_rts)


def create_external_run(ctx, total):
    def run():
        was_trap = 0
        ctx.count = 0
        cycles = 0
        ctx.cpu.pulse_reset()

        while True:
            er = ctx.cpu.execute(100_000)
            cycles += er.cycles
            if er.was_trap:
                was_trap += 1
                res = ctx.traps.call()
                if res is ctx.end_obj:
                    break

        assert was_trap == total + 1
        assert ctx.count == total
        assert cycles == total * 4 + 20  # rts

    return run


def create_internal_run(ctx, total):
    def run():
        ctx.count = 0
        ctx.cpu.pulse_reset()

        res = ctx.mach.execute(100_000)
        assert res.result is ctx.end_obj

        assert ctx.count == total
        assert res.cycles == total * 4 + 20  # rts

    return run


def machine68k_bench_machine_external_exec_benchmark(benchmark):
    ctx = Context()
    total = 10000

    setup_run(ctx, total)
    run = create_external_run(ctx, total)

    benchmark(run)

    ctx.cleanup()


def machine68k_bench_machine_internal_exec_benchmark(benchmark):
    ctx = Context()
    total = 10

    setup_run(ctx, total)
    run = create_internal_run(ctx, total)

    benchmark(run)

    ctx.cleanup()
