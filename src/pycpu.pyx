# cpu type constants
cpdef enum CPUType:
  INVALID = 0
  M68000 = 1
  M68010 = 2
  M68EC020 = 3
  M68020 = 4
  M68EC030 = 5
  M68030 = 6
  M68EC040 = 7
  M68LC040 = 8
  M68040 = 9
  SCC68070 = 10

# register constants
cpdef enum Register:
  D0 = 0
  D1 = 1
  D2 = 2
  D3 = 3
  D4 = 4
  D5 = 5
  D6 = 6
  D7 = 7

  A0 = 8
  A1 = 9
  A2 = 10
  A3 = 11
  A4 = 12
  A5 = 13
  A6 = 14
  A7 = 15

  PC = 16
  SR = 17
  SP = 18
  USP = 19
  ISP = 20
  MSP = 21
  SFC = 22
  DFC = 23
  VBR = 24
  CACR = 25
  CAAR = 26
  PREF_ADDR = 27
  PREF_DATA = 28
  PPC = 29
  IR = 30
  CPU_TYPE = 31

cpdef cpu_type_from_str(name):
  try:
    return CPUType[name]
  except KeyError:
    if name in ("68000", "000", "00"):
      return CPUType.M68000
    elif name in ("68020", "020", "20"):
      return CPUType.M68020
    elif name in ("68030", "030", "30"):
      return CPUType.M68030
    elif name in ("68040", "040", "40"):
      return CPUType.M68040
    else:
      raise ValueError("Invalid CPUType: '%s'" % name)

cpdef cpu_type_to_str(cpu_type):
  if cpu_type == CPUType.M68000:
    return "68000"
  elif cpu_type == CPUType.M68020:
    return "68020"
  elif cpu_type == CPUType.M68030:
    return "68030"
  elif cpu_type == CPUType.M68040:
    return "68040"
  else:
    return None

# exception during execution
cdef object run_exc

cdef clear_run_exc():
  global run_exc
  run_exc = None

cdef raise_run_exc():
  global run_exc
  if run_exc is not None:
    exc = run_exc
    run_exc = None
    raise exc[0], exc[1], exc[2]

# func wrapper
cdef object pc_changed_func
cdef void pc_changed_func_wrapper(unsigned int new_pc) noexcept:
  try:
    pc_changed_func(new_pc)
  except:
    global run_exc
    run_exc = sys.exc_info()
    cpu_end_execute(CPU_END_ERROR)

cdef object reset_instr_func
cdef void reset_instr_func_wrapper() noexcept:
  try:
    reset_instr_func()
  except:
    global run_exc
    run_exc = sys.exc_info()
    cpu_end_execute(CPU_END_ERROR)

cdef object instr_hook_func
cdef void instr_hook_func_wrapper(unsigned int pc) noexcept:
  try:
    instr_hook_func(pc)
  except:
    global run_exc
    run_exc = sys.exc_info()
    cpu_end_execute(CPU_END_ERROR)

# public CPUContext
cdef class CPUContext:
  cdef void *data
  cdef unsigned int size

  def __cinit__(self, unsigned int size):
    self.data = malloc(size)
    if self.data == NULL:
      raise MemoryError()
    self.size = size

  cdef void *get_data(self):
    return self.data

  def r_reg(self, int reg):
    return m68k_get_reg(self.data, <m68k_register_t>reg)

  def r_pc(self):
    return m68k_get_reg(self.data, M68K_REG_PC)

  def r_sp(self):
    return m68k_get_reg(self.data, M68K_REG_SP)

  def r_usp(self):
    return m68k_get_reg(self.data, M68K_REG_USP)

  def r_isp(self):
    return m68k_get_reg(self.data, M68K_REG_ISP)

  def r_msp(self):
    return m68k_get_reg(self.data, M68K_REG_MSP)

  def __dealloc__(self):
    free(self.data)

# public ExecutionResult
@dataclasses.dataclass
cdef class ExecutionResult:
  cdef readonly int cycles
  cdef readonly bint was_trap

# public CPU class
cdef class CPU:
  cdef readonly CPUType cpu_type

  def __cinit__(self, CPUType cpu_type):
    cpu_init(<unsigned int>cpu_type)
    self.cpu_type = cpu_type

  def cleanup(self):
    self.set_pc_changed_callback(None)
    self.set_reset_instr_callback(None)
    self.set_instr_hook_callback(None)

  def __repr__(self):
    return f"CPU(type={cpu_type_to_str(self.cpu_type)})"

  def get_cpu_type(self):
    return self.cpu_type

  def get_cpu_name(self):
    return cpu_type_to_str(self.cpu_type)

  cdef unsigned int r_reg_internal(self, m68k_register_t reg):
    return m68k_get_reg(NULL, reg)

  cdef void w_reg_internal(self, m68k_register_t reg, unsigned int v):
    m68k_set_reg(reg, v)

  # basic register access

  def w_reg(self, reg, unsigned int val):
    self.w_reg_internal(reg,val)

  def r_reg(self,reg):
    return self.r_reg_internal(reg)

  def ws_reg(self, m68k_register_t reg, int val):
    m68k_set_reg(reg, <unsigned int>(val))

  def rs_reg(self, m68k_register_t reg):
    return <int>m68k_get_reg(NULL, reg)

  # unsigned partial update

  def w8_reg(self, reg, unsigned int val):
    if val > 0xff:
      raise OverflowError("Not a ubyte value!")
    reg_val = self.r_reg_internal(reg)
    reg_val = (reg_val & 0xffffff00) | val
    self.w_reg_internal(reg, reg_val)

  def w16_reg(self, reg, unsigned int val):
    if val > 0xffff:
      raise OverflowError("Not a uword value!")
    reg_val = self.r_reg_internal(reg)
    reg_val = (reg_val & 0xffff0000) | val
    self.w_reg_internal(reg, reg_val)

  def w32_reg(self, reg, unsigned int val):
    if val > 0xffffffff:
      raise OverflowError("Not a ulong value!")
    self.w_reg_internal(reg, val & 0xffffffff)

  def r8_reg(self, reg):
    return self.r_reg_internal(reg) & 0xff

  def r16_reg(self, reg):
    return self.r_reg_internal(reg) & 0xffff

  def r32_reg(self, reg):
    return self.r_reg_internal(reg)

  # signed partial update of register

  def w8s_reg(self, reg, int val):
    if val < -0x80 or val >= 0x80:
      raise OverflowError("Not a byte value!")
    reg_val = self.r_reg_internal(reg)
    reg_val = (reg_val & 0xffffff00) | ((<unsigned int>val) & 0xff)
    self.w_reg_internal(reg, reg_val)

  def w16s_reg(self, reg, int val):
    if val < -0x8000 or val >= 0x8000:
      raise OverflowError("Not a word value!")
    reg_val = self.r_reg_internal(reg)
    reg_val = (reg_val & 0xffff0000) | ((<unsigned int>val) & 0xffff)
    self.w_reg_internal(reg, reg_val)

  def w32s_reg(self, reg, int val):
    if val < -0x80000000 or val >= 0x80000000:
      raise OverflowError("Not a long value!")
    self.w_reg_internal(reg, (<unsigned int>val) & 0xffffffff)

  def r8s_reg(self, reg):
    val = <int>self.r_reg_internal(reg)
    return ((val & 0xff) ^ 0x80) - 0x80

  def r16s_reg(self, reg):
    val = <int>self.r_reg_internal(reg)
    return ((val & 0xffff) ^ 0x8000) - 0x8000

  def r32s_reg(self, reg):
    return <int>self.r_reg_internal(reg)

  # special registers

  def w_pc(self, val):
    self.w_reg_internal(M68K_REG_PC,val)

  def r_pc(self):
    return self.r_reg_internal(M68K_REG_PC)

  def w_sp(self, val):
    self.w_reg_internal(M68K_REG_A7,val)

  def r_sp(self):
    return self.r_reg_internal(M68K_REG_A7)

  def w_sr(self, val):
    self.w_reg_internal(M68K_REG_SR,val)

  def r_sr(self):
    return self.r_reg_internal(M68K_REG_SR)

  def w_usp(self, val):
    self.w_reg_internal(M68K_REG_USP,val)

  def r_usp(self):
    return self.r_reg_internal(M68K_REG_USP)

  def w_isp(self, val):
    self.w_reg_internal(M68K_REG_ISP,val)

  def r_isp(self):
    return self.r_reg_internal(M68K_REG_ISP)

  def w_msp(self, val):
    self.w_reg_internal(M68K_REG_MSP,val)

  def r_msp(self):
    return self.r_reg_internal(M68K_REG_MSP)

  # cpu control

  def pulse_reset(self):
    return m68k_pulse_reset()

  def execute(self, num_cycles):
    clear_run_exc()
    cdef int total_cycles
    cdef int flags = cpu_execute(num_cycles, &total_cycles)

    # an error will raise an excpetion
    if (flags & CPU_END_ERROR) != 0:
      raise_run_exc()

    # has trap?
    cdef bint was_trap = (flags & CPU_END_TRAP) != 0

    return ExecutionResult(total_cycles, was_trap)

  # callbacks

  def set_pc_changed_callback(self, py_func):
    global pc_changed_func
    pc_changed_func = py_func
    if py_func is None:
      m68k_set_pc_changed_callback(NULL)
    else:
      m68k_set_pc_changed_callback(pc_changed_func_wrapper)

  def set_reset_instr_callback(self, py_func):
    global reset_instr_func
    reset_instr_func = py_func
    if py_func is None:
      m68k_set_reset_instr_callback(NULL)
    else:
      m68k_set_reset_instr_callback(reset_instr_func_wrapper)

  def set_instr_hook_callback(self, py_func):
    global instr_hook_func
    instr_hook_func = py_func
    if py_func is None:
      m68k_set_instr_hook_callback(NULL)
    else:
      m68k_set_instr_hook_callback(instr_hook_func_wrapper)

  # disassembler

  def disassemble(self, unsigned int pc):
    cdef char line[80]
    cdef unsigned int size
    size = m68k_disassemble(line, pc, self.cpu_type)
    return (size, line.decode('latin-1'))

  def disassemble_raw(self, unsigned int pc, const unsigned char[::1] raw_mem):
    cdef char line[80]
    cdef unsigned int size
    size = m68k_disassemble_raw(line, pc, &raw_mem[0], NULL, self.cpu_type)
    return (size, line.decode('latin-1'))

  # CPU context handling

  def get_cpu_context(self):
    cdef unsigned int size = m68k_context_size()
    cdef CPUContext ctx = CPUContext(size)
    cdef void *data = ctx.get_data()
    m68k_get_context(data)
    return ctx

  def set_cpu_context(self, CPUContext ctx):
    m68k_set_context(ctx.get_data())
