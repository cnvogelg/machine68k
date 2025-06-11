import pytest
from machine68k import Machine, Traps, CPUType


@pytest.fixture(params=["traps", "local", "remote"])
def traps(request):
    mode = request.param
    if mode == "cpu":
        yield Traps()
    elif mode == "local":
        m = Machine(CPUType.M68000, 16)
        yield m.traps
        m.cleanup()
    else:
        rmachine68k = pytest.importorskip("rmachine68k")
        client = request.getfixturevalue("remote_client")
        m = rmachine68k.create_machine(client, "68000", 16)
        yield m.traps


def machine68k_traps_trigger_test(traps):
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func)
    assert tid >= 0
    traps.trigger(tid, 23)
    assert a == [tid, 23]
    traps.free(tid)


def machine68k_traps_raise_test(traps):
    a = []
    b = []

    def my_func(opcode, pc):
        raise ValueError("bla")

    tid = traps.setup(my_func)
    assert tid >= 0
    with pytest.raises(ValueError):
        traps.trigger(tid, 23)
    traps.free(tid)


def machine68k_traps_defer_test(traps):
    a = []

    def my_func(opcode, pc):
        a.append(opcode)
        a.append(pc)

    tid = traps.setup(my_func, defer=True)
    assert tid >= 0

    # a trigger does not call the trap
    traps.trigger(tid, 23)
    assert a == []
    # now trigger deferred call
    traps.defer_call()
    assert a == [tid, 23]

    traps.free(tid)


def machine68k_traps_defer_raise_test(traps):
    def my_func(opcode, pc):
        raise ValueError("bla")

    tid = traps.setup(my_func, defer=True)
    assert tid >= 0

    # a trigger does not call the trap
    traps.trigger(tid, 23)
    # now trigger deferred call
    with pytest.raises(ValueError):
        traps.defer_call()

    traps.free(tid)
