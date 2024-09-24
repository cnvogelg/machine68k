cdef int trap_wrapper(uint opcode, uint pc, void *data) noexcept:
  global trap_exc
  cdef object py_func = <object>data
  try:
    py_func(opcode, pc)
    return TRAP_RESULT_OK
  except:
    global run_exc
    run_exc = sys.exc_info()
    return TRAP_RESULT_ERROR

cdef class Traps:
  cdef dict func_map

  def __cinit__(self):
    trap_init()
    self.func_map = {}

  def setup(self, py_func, auto_rts=False, one_shot=False, defer=False):
    cdef int flags
    flags = TRAP_FLAG_DEFAULT
    if auto_rts:
      flags |= TRAP_FLAG_AUTO_RTS
    if one_shot:
      flags |= TRAP_FLAG_ONE_SHOT
    if defer:
      flags |= TRAP_FLAG_DEFER
    tid = trap_setup(trap_wrapper, flags, <void *>py_func)
    if tid != -1:
      # keep function reference around
      self.func_map[tid] = py_func
    return tid

  def free(self, tid):
    trap_free(tid)
    del self.func_map[tid]

  def trigger(self, uint opcode, uint pc):
    clear_run_exc()
    cdef int result = trap_aline(opcode, pc)
    raise_run_exc()
    return result

  def defer_call(self):
    clear_run_exc()
    cdef int result = trap_defer_call()
    if result != TRAP_RESULT_OK:
      raise_run_exc()

  def get_func(self, tid):
    if tid in self.func_map:
      return self.func_map[tid]
