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

#define MAX_NESTING 16

#define RUN_MODE_IDLE          0
#define RUN_MODE_EXECUTE       1
#define RUN_MODE_DEFER_TRAP    2

typedef struct state {
  int end_flags;
  int cycles;
  int run_mode;
  int nesting;
} state_t;

static state_t states[MAX_NESTING];
static state_t *cur_state;
static int nesting;

static void init_state(state_t *state)
{
  state->end_flags = 0;
  state->cycles = 0;
  state->run_mode = RUN_MODE_IDLE;
}

void cpu_init(void)
{
  nesting = 0;
  for(int i=0;i<MAX_NESTING;i++) {
    states[i].nesting = i;
  }

  cur_state = &states[0];
  init_state(cur_state);
}

void cpu_end(int flag)
{
  if(cur_state->end_flags == 0) {
    m68k_end_timeslice();
  }

  cur_state->end_flags |= flag;
  D(("#%d cpu_end %08x\n", cur_state->nesting, cur_state->end_flags));
}

int cpu_execute(int max_cycles, int *got_cycles)
{
  /* make sure we do not recurse while runnning m68k_execute()!
     use deferred traps for that. */
  if(cur_state->run_mode == RUN_MODE_EXECUTE) {
    return CPU_END_RECURSE_EXECUTE;
  }

  /* nesting */
  int nested = 0;
  if(cur_state->run_mode == RUN_MODE_DEFER_TRAP) {
    if(nesting == (MAX_NESTING - 1)) {
      return CPU_END_NESTING_TOO_DEEP;
    }

    nesting++;
    cur_state = &states[nesting];
    nested = 1;
  }

  init_state(cur_state);

  D(("#%d exec loop begin\n", cur_state->nesting));
  while(1) {
    /* clear end flag for this run */
    cur_state->end_flags = 0;
    cur_state->run_mode = RUN_MODE_EXECUTE;

    /* call musashi CPU emulator.
       callbacks triggered here might set end_flags and
       end the time slice.
       otherwise it will only return if the cycles are
       used up.
    */
    D(("#%d begin execute. max=%d cycles=%d pc=%x\n",
      cur_state->nesting, max_cycles, cur_state->cycles,
      m68k_get_reg(NULL, M68K_REG_PC)));

    int cycles = m68k_execute(max_cycles);
    cur_state->cycles += cycles;

    D(("#%d end execute. cyc=%d cycles=%d pc=%x\n",
      cur_state->nesting, cycles, cur_state->cycles,
      m68k_get_reg(NULL, M68K_REG_PC)));

    /* if an error occurred then abort right now.
       do not call any deferred traps.
       the deferred trap is still there.
       it may be called manually later on with trap_defer_call()
       but usually you don't need it anyway.
    */
    if(cur_state->end_flags & CPU_END_ERROR_MASK) {
      break;
    }

    /* check for deferred trap */
    if(cur_state->end_flags & CPU_END_TRAP_DEFER) {
      /* remove flag */
      cur_state->end_flags &= ~CPU_END_TRAP_DEFER;

      cur_state->run_mode = RUN_MODE_DEFER_TRAP;

      /* execute trap now deferred after execute().
         here a recursive cpu_execute() might happen...
      */
      int result = trap_defer_call();

      /* if trap failed then set error flag */
      if(result != TRAP_RESULT_OK) {
        cur_state->end_flags |= CPU_END_TRAP_ERROR;
      }
    }

    max_cycles -= cycles;

    /* no more cycles left? */
    if(max_cycles <= 0) {
      cur_state->end_flags |= CPU_END_MAX_CYCLES;
      break;
    }

    /* end run? */
    if(cur_state->end_flags != 0) {
      break;
    }
  }
  D(("#%d exec loop end: %x\n", cur_state->nesting, cur_state->end_flags));

  /* return total cycles */
  if(got_cycles != NULL) {
    *got_cycles = cur_state->cycles;
  }
  int end_flags = cur_state->end_flags;

  cur_state->cycles = 0;
  cur_state->run_mode = RUN_MODE_IDLE;

  if(nested) {
    nesting--;
    cur_state = &states[nesting];
  }

  return end_flags;
}

int cpu_cycles_run(void)
{
  int cycles = cur_state->cycles;
  if(cur_state->run_mode == RUN_MODE_EXECUTE) {
    cycles += m68k_cycles_run();
  }
  return cycles;
}
