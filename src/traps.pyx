# traps.h
cdef extern from "traps.h":
  ctypedef struct trap_info_t:
    unsigned int opcode
    unsigned int pc
    unsigned int offset
    void *data

  void trap_init()
  int  trap_alloc(void *data)
  void trap_free(int id)
  void *trap_get_data(int id)

  # for testing
  int trap_trigger(uint opcode, uint pc)
  trap_info_t *trap_get_info()
