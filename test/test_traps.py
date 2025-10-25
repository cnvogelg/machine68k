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
        return "hello"

    # alloc trap
    tid = traps.alloc(my_func)
    assert tid >= 0
    # check func
    assert traps.get_func(tid) is my_func
    assert traps.get_func(tid + 1) is None
    # simulate trigger by CPU execution
    traps.trigger(tid, 23)
    # check info
    info = traps.get_info()
    assert info.pc == 23
    assert info.offset == tid
    assert info.func is my_func
    # trigger the call
    result = traps.call()
    assert result == "hello"
    assert a == [tid, 23]
    # release trap
    traps.free(tid)


def machine68k_traps_raise_test(traps):
    a = []
    b = []

    def my_func(opcode, pc):
        raise ValueError("bla")

    # alloc trap
    tid = traps.alloc(my_func)
    assert tid >= 0
    # simulate trigger
    traps.trigger(tid, 23)
    # check info
    info = traps.get_info()
    assert info.pc == 23
    assert info.offset == tid
    assert info.func is my_func
    # trigger call and expect exception
    with pytest.raises(ValueError):
        traps.call()
    # free trap
    traps.free(tid)


def machine68k_traps_return_test(traps):
    a = []
    b = []

    class Mine:
        pass

    mine = Mine()

    def my_func(opcode, pc):
        return mine

    # alloc trap
    tid = traps.alloc(my_func)
    assert tid >= 0
    # simulate trap trigger
    traps.trigger(tid, 23)
    # check info
    info = traps.get_info()
    assert info.pc == 23
    assert info.offset == tid
    assert info.func is my_func
    # trigger call and expect return value
    assert traps.call() is mine
    # free trap
    traps.free(tid)
