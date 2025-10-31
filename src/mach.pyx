# string.h
from libc.string cimport memcpy, memset, strlen, strcpy
# stdlib.h
from libc.stdlib cimport malloc, free

from cpython.bytes cimport PyBytes_FromStringAndSize

import sys
import dataclasses

include "m68k.pyx"
include "cpu.pyx"
include "mem.pyx"
include "traps.pyx"

include "pycpu.pyx"
include "pymem.pyx"
include "pytraps.pyx"

@dataclasses.dataclass
cdef class MachineExecutionResult:
  cdef readonly int cycles
  cdef readonly bint exit

cdef class Machine:
  cdef readonly CPU cpu
  cdef readonly Memory mem
  cdef readonly Traps traps
  cdef int _exit_trap
  cdef unsigned int _exit_addr

  def __cinit__(self, CPUType cpu_type, unsigned ram_size_kb):
    self.cpu = CPU(cpu_type)
    self.mem = Memory(ram_size_kb)
    self.traps = Traps()

  def cleanup(self):
    self.cpu.cleanup()
    self.mem.cleanup()
    self.traps.cleanup()

  def __repr__(self):
    return f"Machine({self.cpu},{self.mem})"

  def init_execute(self, exit_addr):
    def exit_handler(opcode, pc):
      # self is our sentinel for the exit trap
      return self
    self._exit_addr = exit_addr
    self._exit_trap = self.traps.alloc(exit_handler)
    # place trap 
    opc = 0xa000 | self._exit_trap
    self.mem.w16(self._exit_addr, opc)
  
  def exit_execute(self):
    self.traps.free(self._exit_trap)

  def prepare_execute(self, pc, sp):
    self.cpu.w_pc(pc)
    # place end trap on stack
    sp -= 4
    self.mem.w32(sp, self._exit_addr)
    self.cpu.w_sp(sp)

  def execute(self, max_cycles=1000):
    clear_run_exc()
    cdef bint exit = False
    cdef int total_cycles = 0
    cdef int flags = cpu_execute(max_cycles, &total_cycles)

    # an error will raise an excpetion
    if (flags & CPU_END_ERROR) != 0:
      raise_run_exc()

    # has trap?
    if (flags & CPU_END_TRAP) != 0:
      res = self.traps.call()
      # exit?
      if res is self:
          exit = True
 
    return MachineExecutionResult(total_cycles, exit)
