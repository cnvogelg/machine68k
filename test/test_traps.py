import sys
from machine68k import Traps


def machine68k_traps_trigger_test():
    traps = Traps()
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func)
    assert tid >= 0
    traps.trigger(tid, 23)
    assert a == [tid, 23]
    traps.free(tid)


def machine68k_traps_raise_test():
    traps = Traps()
    a = []
    b = []

    def exc_func(opcode, pc):
        a.append(opcode)
        a.append(pc)
        b.append(sys.exc_info())

    traps.set_exc_func(exc_func)

    def my_func(opcode, pc):
        raise ValueError("bla")

    tid = traps.setup(my_func)
    assert tid >= 0
    traps.trigger(tid, 23)
    assert a == [tid, 23]
    assert b[0][0] == ValueError
    traps.free(tid)
