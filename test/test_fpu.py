from machine68k import CPUType, Machine, Register


def machine68k_fpu_extended_exponent_zero_test():
    mach = Machine(CPUType.M68040, 16)
    mem = mach.mem
    cpu = mach.cpu

    def write_extended(addr, exponent, mantissa_high, mantissa_low):
        mem.w16(addr, exponent)
        mem.w16(addr + 2, 0)
        mem.w32(addr + 4, mantissa_high)
        mem.w32(addr + 8, mantissa_low)

    def read_extended(addr):
        return (
            mem.r16(addr),
            mem.r16(addr + 2),
            mem.r32(addr + 4),
            mem.r32(addr + 8),
        )

    write_extended(0x300, 0, 0x80000000, 0)
    write_extended(0x310, 0x3FFF, 0x80000000, 0)
    write_extended(0x340, 0, 0, 1)
    write_extended(0x360, 0x7FFF, 0, 0)
    write_extended(0x380, 0x4000, 0xC0000000, 0)
    write_extended(0x390, 0x3FFE, 0x80000000, 0)
    write_extended(0x3B0, 1, 0x80000000, 0)

    instructions = [
        (0xF210, 0x4800),  # FMOVE.X (A0), FP0
        (0xF211, 0x4823),  # FMUL.X (A1), FP0
        (0xF212, 0x6800),  # FMOVE.X FP0, (A2)
        (0xF210, 0x4800),
        (0xF210, 0x4822),  # FADD.X (A0), FP0
        (0xF213, 0x6800),  # FMOVE.X FP0, (A3)
        (0xF210, 0x4800),
        (0xF211, 0x4823),
        (0xF212, 0x6800),  # FMOVE.X FP0, (A2)
        (0xF210, 0x4800),
        (0xF211, 0x4828),  # FSUB.X (A1), FP0
        (0xF212, 0x6800),
        (0xF214, 0x4800),  # FMOVE.X (A4), FP0
        (0xF211, 0x4823),
        (0xF215, 0x6800),  # FMOVE.X FP0, (A5)
        (0xF216, 0x4800),  # FMOVE.X (A6), FP0
        (0xF211, 0x4823),
        (0xF217, 0x6800),  # FMOVE.X FP0, (A7)
        (0xF211, 0x4800),  # FMOVE.X (A1), FP0
        (0xF210, 0x4820),  # FDIV.X (A0), FP0
        (0xF216, 0x6800),  # FMOVE.X FP0, (A6)
    ]

    for i, (opcode, extension) in enumerate(instructions):
        mem.w16(0x100 + i * 4, opcode)
        mem.w16(0x102 + i * 4, extension)

    cpu.w_reg(Register.PC, 0x100)
    for reg, addr in enumerate(
        [0x300, 0x310, 0x320, 0x330, 0x340, 0x350, 0x360, 0x370]
    ):
        cpu.w_reg(Register.A0 + reg, addr)

    try:
        for _ in instructions[:6]:
            cpu.execute(1)

        cpu.w_reg(Register.A1, 0x390)
        cpu.w_reg(Register.A2, 0x3A0)
        for _ in instructions[6:9]:
            cpu.execute(1)

        cpu.w_reg(Register.A0, 0x3B0)
        cpu.w_reg(Register.A1, 0x340)
        cpu.w_reg(Register.A2, 0x3C0)
        for _ in instructions[9:12]:
            cpu.execute(1)

        cpu.w_reg(Register.A0, 0x380)
        cpu.w_reg(Register.A1, 0x310)
        cpu.w_reg(Register.A2, 0x320)
        for _ in instructions[12:]:
            cpu.execute(1)

        assert read_extended(0x320) == (0, 0, 0x80000000, 0)
        assert read_extended(0x330) == (1, 0, 0x80000000, 0)
        assert read_extended(0x3A0) == (0, 0, 0x40000000, 0)
        assert read_extended(0x3C0) == (0, 0, 0xFFFFFFFF, 0xFFFFFFFF)
        assert read_extended(0x350) == (0, 0, 0, 1)
        assert read_extended(0x370) == (0x7FFF, 0, 0, 0)
        assert read_extended(0x360) == (0x3FFD, 0, 0xAAAAAAAA, 0xAAAAAAAB)
    finally:
        mach.cleanup()
