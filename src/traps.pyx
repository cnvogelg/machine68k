# traps.h
cdef extern from "traps.h":
  int TRAP_FLAG_DEFAULT
  int TRAP_FLAG_AUTO_RTS
  int TRAP_FLAG_ONE_SHOT
  int TRAP_FLAG_DEFER

  int TRAP_RESULT_OK
  int TRAP_RESULT_ERROR

  ctypedef int (*trap_func_t)(uint opcode, uint pc, void *data)

  void trap_init()
  int  trap_setup(trap_func_t func, int flags, void *data)
  void trap_free(int id)

  # for testing
  int trap_aline(uint opcode, uint pc)
  int trap_defer_call()
