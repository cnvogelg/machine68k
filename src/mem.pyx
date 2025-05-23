# mem.h
cdef extern from "mem.h":
  ctypedef uint (*read_func_t)(uint addr, void *ctx)
  ctypedef void (*write_func_t)(uint addr, uint value, void *ctx)
  ctypedef void (*invalid_func_t)(int mode, int width, uint addr, void *ctx)
  ctypedef void (*trace_func_t)(int mode, int width, uint addr, uint val, void *ctx)

  int mem_init(uint ram_size_kib, void *own_ram)
  void mem_free()

  void mem_set_invalid_func(invalid_func_t func, void *ctx)
  void mem_set_trace_mode(int on)
  void mem_set_trace_func(trace_func_t func, void *ctx)

  uint mem_reserve_special_range(uint num_pages)
  void mem_set_special_range_read_func(uint page_addr, uint width, read_func_t func, void *ctx)
  void mem_set_special_range_write_func(uint page_addr, uint width, write_func_t func, void *ctx)

  unsigned int m68k_read_memory_8(unsigned int address)
  unsigned int m68k_read_memory_16(unsigned int address)
  unsigned int m68k_read_memory_32(unsigned int address)

  void m68k_write_memory_8(unsigned int address, unsigned int value)
  void m68k_write_memory_16(unsigned int address, unsigned int value)
  void m68k_write_memory_32(unsigned int address, unsigned int value)

  unsigned char *mem_raw_ptr()
  uint mem_raw_size()

  int mem_ram_r8(uint addr, uint *val)
  int mem_ram_r16(uint addr, uint *val)
  int mem_ram_r32(uint addr, uint *val)

  int mem_ram_w8(uint addr, uint val)
  int mem_ram_w16(uint addr, uint val)
  int mem_ram_w32(uint addr, uint val)

