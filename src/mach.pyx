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
  cdef readonly int sum_cycles
  cdef readonly MachineEndExecution result

@dataclasses.dataclass
cdef class MachineState:
  cdef int cycles
  cdef int sum_cycles
  cdef MachineEndExecution abort

cdef class Machine:
  cdef readonly CPU cpu
  cdef readonly Memory mem
  cdef readonly Traps traps
  cdef readonly list state_stack
  cdef readonly MachineEndExecution abort_default

  def __cinit__(self, CPUType cpu_type, unsigned ram_size_kb):
    self.cpu = CPU(cpu_type)
    self.mem = Memory(ram_size_kb)
    self.traps = Traps()
    self.state_stack = []
    self.abort_default = MachineEndExecution("abort")

  def cleanup(self):
    self.cpu.cleanup()
    self.mem.cleanup()
    self.traps.cleanup()

  def __repr__(self):
    return f"Machine({self.cpu},{self.mem})"

  def create_execute_end(self, str desc):
    """create an object that will end the execution"""
    return MachineEndExecution(desc)

  def get_abort_default(self):
    """return the default result object when a run was aborted"""
    return self.abort_default

  def abort_execute(self, abort_obj=None):
    """abort the current execution from trap code"""
    cdef MachineState state
    
    if len(self.state_stack) > 0:
      if abort_obj is None:
        abort_obj = self.abort_default
      state = self.state_stack[-1]
      state.abort = abort_obj
      return True
    else:
      return False

  def get_state(self):
    """return current state inside an execute run"""
    cdef MachineState state
    if len(self.state_stack) > 0:
      state = self.state_stack[-1]
      return MachineExecutionResult(state.cycles, 
                                    state.sum_cycles,
                                    state.abort)
    else:
      return None

  def get_nesting_level(self):
    """nesting level"""
    return len(self.state_stack)

  def execute(self, int max_cycles=1000):
    """main execution call. 

        run up to max_cycles. trigger traps.
        end the execution early if an exception was raised
        or a trap_end_res was returned by a trap
        or abort_execution() was called by a trap.
    """
    cdef MachineEndExecution exit = None
    cdef int run_cycles = 0
    cdef int total_cycles = 0
    cdef int flags
    cdef MachineState state = MachineState(0, 0, None)
    cdef MachineState last_state
    cdef object exc = None
    cdef object trace_back = None

    # take over cycles from last state if any
    if len(self.state_stack) > 0:
      last_state = self.state_stack[-1]
      state.sum_cycles = last_state.sum_cycles

    # push a new machine state on the stack
    self.state_stack.append(state)

    # track execptions from callbacks inside 
    clear_run_exc()

    while total_cycles < max_cycles:
      
      # let the CPU run
      run_cycles = 0
      flags = cpu_execute(max_cycles, &run_cycles)
      
      # account cycles, so that code in a trap can query it
      # via get_current_cycles()
      state.cycles += run_cycles
      state.sum_cycles += run_cycles
      total_cycles += run_cycles

      # an error will raise an excpetion
      if (flags & CPU_END_ERROR) != 0:
        raise_run_exc()
        break

      # has trap?
      if (flags & CPU_END_TRAP) != 0:
        # call trap
        try:
          res = self.traps.call()
          # return value of trap is an end obj
          if type(res) is MachineEndExecution:
            exit = res
            break
        # exception happened. leave loop
        except Exception as trap_exc:
          exc = trap_exc
          trace_back = sys.exc_info()[2]
          break

        # was abort_execute() triggered inside trap?
        if state.abort:
          exit = state.abort
          break

    # pop current state
    self.state_stack.pop()

    # adjust sum cycles of previous run
    if len(self.state_stack) > 0:
      last_state = self.state_stack[-1]
      last_state.sum_cycles += state.cycles

    # now raise trap exception
    if exc:
      raise exc.with_traceback(trace_back)

    return MachineExecutionResult(state.cycles, state.sum_cycles, exit)
