@dataclasses.dataclass
cdef class TrapInfo:
  cdef readonly unsigned int opcode
  cdef readonly unsigned int pc
  cdef readonly unsigned int offset
  cdef readonly object func
  cdef readonly bint old_pc

cdef class Traps:
  cdef dict func_map

  def __cinit__(self):
    trap_init()
    self.func_map = {}

  def cleanup(self):
    pass

  def __repr__(self):
    return f"Traps(num={len(self.func_map)})"

  def alloc(self, py_func, old_pc=False):
    cdef int flags
    flags = TRAP_FLAG_DEFAULT
    if old_pc:
      flags |= TRAP_FLAG_OLD_PC

    tid = trap_alloc(flags, <void *>py_func)
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
    cdef bint old_pc = (ti.flags & TRAP_FLAG_OLD_PC) != 0
    return TrapInfo(
      ti.opcode,
      ti.pc,
      ti.offset,
      func,
      old_pc
    )
  
  cpdef call(self):
    cdef unsigned int cur_pc 
    cdef trap_info_t *ti = trap_get_info()
    cdef object func = <object>ti.data
    if not func:
      raise RuntimeError("Invalid trap!")
    
    if (ti.flags & TRAP_FLAG_OLD_PC) != 0:
      cur_pc = m68k_get_reg(NULL, M68K_REG_PC);
      m68k_set_reg(M68K_REG_PC, ti.pc);
      result = func(ti.opcode, ti.pc)
      m68k_set_reg(M68K_REG_PC, cur_pc);
    else:
      result = func(ti.opcode, ti.pc)

    return result
