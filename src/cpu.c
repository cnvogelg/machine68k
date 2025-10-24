/* more elaborate cpu execution with status handling
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include "m68k.h"
#include <string.h>
#include <stdio.h>

#include "cpu.h"
#include "traps.h"

//#define DEBUG
#ifdef DEBUG
#define D(x) printf x
#else
#define D(x)
#endif

static int run_flags;

void cpu_init(unsigned int cpu_type)
{
  m68k_set_cpu_type(cpu_type);
  m68k_init();
}

void cpu_end_execute(int flag)
{
  run_flags |= flag;
  m68k_end_timeslice();
  D(("cpu_end_execute %x\n", run_flags));
}

int cpu_execute(int max_cycles, int *got_cycles)
{
  run_flags = 0;

  D(("cpu_execute: begin max_cycles=%d pc=%x\n",
    max_cycles, m68k_get_reg(NULL, M68K_REG_PC)));

  /* let the CPU run */
  int cycles = m68k_execute(max_cycles);

  D(("cpu_execute: end cycles=%d pc=%x\n",
    cycles, m68k_get_reg(NULL, M68K_REG_PC)));

  /* store cycles */
  if(got_cycles != NULL) {
    *got_cycles = cycles;
  }

  return run_flags;
}
