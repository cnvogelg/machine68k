# string.h
from libc.string cimport memcpy, memset, strlen, strcpy
# stdlib.h
from libc.stdlib cimport malloc, free

import sys

include "m68k.pyx"
include "cpu.pyx"
include "mem.pyx"
include "traps.pyx"

include "pycpu.pyx"
include "pymem.pyx"
include "pytraps.pyx"

cdef class Machine:
  cdef readonly CPU cpu
  cdef readonly Memory mem
  cdef readonly Traps traps

  def __cinit__(self, CPUType cpu_type, unsigned ram_size_kb):
    self.cpu = CPU(cpu_type)
    self.mem = Memory(ram_size_kb)
    self.traps = Traps()

  def cleanup(self):
    self.cpu.cleanup()
    self.mem.cleanup()
    self.traps.cleanup()
