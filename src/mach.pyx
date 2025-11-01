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
cdef class MachineEndExecution:
  cdef readonly str desc

@dataclasses.dataclass
cdef class MachineExecutionResult:
  cdef readonly int cycles
  cdef readonly MachineEndExecution trap_res

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

  def create_trap_res(self, str desc):
    return MachineEndExecution(desc)

  def execute(self, int max_cycles=1000):
    cdef MachineEndExecution exit = None
    cdef int run_cycles = 0
    cdef int flags

    clear_run_exc()

    flags = cpu_execute(max_cycles, &run_cycles)

    # an error will raise an excpetion
    if (flags & CPU_END_ERROR) != 0:
      raise_run_exc()

    # has trap?
    if (flags & CPU_END_TRAP) != 0:
      res = self.traps.call()
      # exit?
      if type(res) is MachineEndExecution:
          exit = res
 
    return MachineExecutionResult(run_cycles, exit)
