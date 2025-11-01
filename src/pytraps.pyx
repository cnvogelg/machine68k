@dataclasses.dataclass
cdef class TrapInfo:
  cdef readonly unsigned int opcode
  cdef readonly unsigned int pc
  cdef readonly unsigned int offset
  cdef readonly object func

cdef class Traps:
  cdef dict func_map

  def __cinit__(self):
    trap_init()
    self.func_map = {}

  def cleanup(self):
    pass

  def __repr__(self):
    return f"Traps(num={len(self.func_map)})"

  def alloc(self, py_func):
    tid = trap_alloc(<void *>py_func)
    if tid != -1:
      # keep function reference around
      self.func_map[tid] = py_func

    return tid

  def free(self, tid):
    trap_free(tid)
    del self.func_map[tid]

  def get_func(self, tid):
    cdef void *data = trap_get_data(tid)
    if data == NULL:
      return None
    else:
      return <object>data

  def trigger(self, uint opcode, uint pc):
    cdef int result = trap_trigger(opcode, pc)
    return result

  def get_info(self):
    cdef trap_info_t *ti = trap_get_info()
    cdef object func = <object>ti.data
    return TrapInfo(
      ti.opcode,
      ti.pc,
      ti.offset,
      func,
    )
  
  cpdef call(self):
    cdef trap_info_t *ti = trap_get_info()
    cdef object func = <object>ti.data
    if not func:
      raise RuntimeError("Invalid trap!")
    return func(ti.opcode, ti.pc)
