/* a dispatcher for a-line opcodes to be used as traps in vamos
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#ifndef _TRAPS_H
#define _TRAPS_H

#include "m68k.h"
#include <stdint.h>

/* Trap Flags */
#define TRAP_FLAG_DEFAULT       0
#define TRAP_FLAG_OLD_PC        1

/* ------ Types ----- */
#ifndef UINT_TYPE
#define UINT_TYPE
typedef unsigned int uint;
#endif

struct trap_info {
  unsigned int opcode;
  unsigned int pc;
  unsigned int offset;
  void *data;
  int flags;
};
typedef struct trap_info trap_info_t;

/* ----- API ----- */
extern void trap_init(void);

extern int  trap_alloc(int flags, void *data);
extern void trap_free(int id);
extern void *trap_get_data(int id);

extern int trap_trigger(uint opcode, uint pc);
extern trap_info_t *trap_get_info(void);

#endif
