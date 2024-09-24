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

static int end_flags;
static int execute_lock;

void cpu_end(int flag)
{
  if(end_flags == 0) {
    m68k_end_timeslice();
  }

  end_flags |= flag;
  D((" cpu_end %08x\n", end_flags));
}

int cpu_execute(int max_cycles, int *got_cycles)
{
  /* make sure we do not recurse while runnning m68k_execute()!
     use deferred traps for that. */
  if(execute_lock) {
    return CPU_END_RECURSE_EXECUTE;
  }

  int total_cycles = 0;
  int local_end_flags = 0;
  D(("exec loop begin\n"));
  while(1) {
    /* clear end flag for this run */
    end_flags = 0;

    /* set a lock */
    execute_lock = 1;

    /* call musashi CPU emulator.
       callbacks triggered here might set end_flags and
       end the time slice.
       otherwise it will only return if the cycles are
       used up.
    */
    D((" begin execute. max=%d pc=%x\n", max_cycles, m68k_get_reg(NULL, M68K_REG_PC)));
    int cycles = m68k_execute(max_cycles);
    D((" end execute. cyc=%d pc=%x\n", cycles, m68k_get_reg(NULL, M68K_REG_PC)));

    /* release lock */
    execute_lock = 0;

    total_cycles += cycles;

    /* copy end_flags into own local copy right now
       since a deferred trap might call cpu_execute() recursively
       and overwrite end_flags.
    */
    local_end_flags = end_flags;

    /* if an error occurred then abort right now.
       do not call any deferred traps.
       the deferred trap is still there.
       it may be called manually later on with trap_defer_call()
       but usually you don't need it anyway.
    */
    if(local_end_flags & CPU_END_ERROR_MASK) {
      break;
    }

    /* check for deferred trap */
    if(local_end_flags & CPU_END_TRAP_DEFER) {
      /* remove flag */
      local_end_flags &= ~CPU_END_TRAP_DEFER;

      /* execute trap now deferred after execute().
         here a recursive cpu_execute() might happen...
      */
      int result = trap_defer_call();

      /* if trap failed then set error flag */
      if(result != TRAP_RESULT_OK) {
        local_end_flags |= CPU_END_TRAP_ERROR;
      }
    }

    /* no more cycles left? */
    if(max_cycles < cycles) {
      local_end_flags |= CPU_END_MAX_CYCLES;
      break;
    }

    /* end run? */
    if(local_end_flags != 0) {
      break;
    }

    max_cycles -= cycles;
  }
  D(("exec loop end: %x\n", local_end_flags));

  /* return total cycles */
  if(got_cycles != NULL) {
    *got_cycles = total_cycles;
  }

  return local_end_flags;
}
