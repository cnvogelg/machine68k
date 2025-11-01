/* a dispatcher for a-line opcodes to be used as traps in vamos
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include "m68k.h"
#include <string.h>
#include <stdio.h>

#include "traps.h"
#include "cpu.h"

#define NUM_TRAPS  0x1000
#define TRAP_MASK  0x0fff

struct entry {
  struct entry *next;
  void *data;
};
typedef struct entry entry_t;

static entry_t traps[NUM_TRAPS];
static entry_t *first_free;
static trap_info_t info;

int trap_trigger(uint opcode, uint pc)
{
  uint off = opcode & TRAP_MASK;
  void *data = traps[off].data;

  /* unbound trap? */
  if(data == NULL) {
    /* regular m68k ALINE exception */
    return M68K_ALINE_EXCEPT;
  }

  /* a trap is not executed in the m68k_execute() loop.
     it is stored, the execution timeslice is ended and afterwards
     the trap will be executed. It is useful for nesting m68k runs
     without recursion of m68k_execute().
  */

  /* keep call */
  info.opcode = opcode;
  info.pc = pc;
  info.offset = off;
  info.data = data;

  /* end slice so we can call the trap directly after execute() */
  cpu_end_execute(CPU_END_TRAP);

  return M68K_ALINE_NONE;
}

trap_info_t *trap_get_info(void)
{
  return &info;
}

void trap_init(void)
{
  int i;

  /* setup free list */
  first_free = &traps[0];
  for(i=0;i<(NUM_TRAPS-1);i++) {
    traps[i].next = &traps[i+1];
    traps[i].data = NULL;
  }
  traps[NUM_TRAPS-1].next = NULL;
  traps[NUM_TRAPS-1].data = NULL;

  /* setup my trap handler */
  m68k_set_aline_hook_callback(trap_trigger);
}

void *trap_get_data(int id)
{
  if((id >= 0) && (id < NUM_TRAPS)) {
    return traps[id].data;
  } else {
    return NULL;
  }
}

int trap_alloc(void *data)
{
  int off;

  /* no more traps available? */
  if(first_free == NULL) {
    return -1;
  }

  off = (int)(first_free - traps);

  /* new first free */
  first_free = traps[off].next;

  /* store trap function */
  traps[off].data = data;

  return off;
}

void trap_free(int id)
{
  /* insert trap into free list */
  traps[id].next = first_free;
  traps[id].data = NULL;
  first_free = &traps[id];
}
