# cpu.h
cdef extern from "cpu.h":
  ctypedef unsigned int uint
  int CPU_END_TRAP
  int CPU_END_ERROR

  void cpu_init(unsigned int cpu_type)
  void cpu_end_execute(int flag)
  int cpu_execute(int max_cycles, int *got_cycles)
