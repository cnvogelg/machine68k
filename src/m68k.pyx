# m68k.h
cdef extern from "m68k.h":
  ctypedef enum m68k_register_t:
    M68K_REG_D0, M68K_REG_D1, M68K_REG_D2, M68K_REG_D3,
    M68K_REG_D4, M68K_REG_D5, M68K_REG_D6, M68K_REG_D7,
    M68K_REG_A0, M68K_REG_A1, M68K_REG_A2, M68K_REG_A3,
    M68K_REG_A4, M68K_REG_A5, M68K_REG_A6, M68K_REG_A7,
    M68K_REG_PC, M68K_REG_SR,
    M68K_REG_SP, M68K_REG_USP, M68K_REG_ISP, M68K_REG_MSP,
    M68K_REG_SFC, M68K_REG_DFC,
    M68K_REG_VBR,
    M68K_REG_CACR, M68K_REG_CAAR,
    M68K_REG_PREF_ADDR, M68K_REG_PREF_DATA,
    M68K_REG_PPC, M68K_REG_IR,
    M68K_REG_CPU_TYPE

  void m68k_set_cpu_type(unsigned int cpu_type)
  void m68k_init()
  int m68k_pulse_reset()
  int m68k_execute(int num_cycles)
  void m68k_end_timeslice()
  int m68k_cycles_run()

  unsigned int m68k_get_reg(void* context, m68k_register_t reg)
  void m68k_set_reg(m68k_register_t reg, unsigned int value)

  void m68k_set_pc_changed_callback(void (*callback)(unsigned int new_pc))
  void m68k_set_reset_instr_callback(void (*callback)())
  void m68k_set_illg_instr_callback(int (*callback)(int opcode))
  void m68k_set_instr_hook_callback(void (*callback)(unsigned int pc))

  unsigned int m68k_disassemble(char* str_buff, unsigned int pc, unsigned int cpu_type)
  unsigned int m68k_disassemble_raw(char* str_buff, unsigned int pc, const unsigned char* opdata, const unsigned char* argdata, unsigned int cpu_type)

  unsigned int m68k_context_size()
  unsigned int m68k_get_context(void* dst)
  void m68k_set_context(void* dst)

