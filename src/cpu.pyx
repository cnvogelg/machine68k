# cpu.h
cdef extern from "cpu.h":
  ctypedef unsigned int uint
  int CPU_END_MAX_CYCLES
  int CPU_END_USER
  int CPU_END_TRAP_DEFER

  int CPU_END_TRAP_ERROR
  int CPU_END_PC_CHANGED_FUNC_ERROR
  int CPU_END_RESET_INSTR_FUNC_ERROR
  int CPU_END_INSTR_HOOK_FUNC_ERROR
  int CPU_END_MEM_TRACE_FUNC_ERROR
  int CPU_END_MEM_INVALID_FUNC_ERROR
  int CPU_END_MEM_READ_FUNC_ERROR
  int CPU_END_MEM_WRITE_FUNC_ERROR

  int CPU_END_RECURSE_EXECUTE
  int CPU_END_ERROR_MASK

  void cpu_end(int flag)
  int cpu_execute(int max_cycles, int *got_cycles);
