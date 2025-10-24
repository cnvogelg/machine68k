/* more elaborate cpu execution with status handling
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#ifndef _CPU_H
#define _CPU_H

#include "m68k.h"
#include <stdint.h>

#ifndef UINT_TYPE
#define UINT_TYPE
typedef unsigned int uint;
#endif

/* Run Flags set by traps/mem during execute() */
#define CPU_END_TRAP           0x0001
#define CPU_END_ERROR          0x0002

extern void cpu_init(unsigned int cpu_type);

/* return cycles (up to max_cycles) */
extern int cpu_execute(int max_cycles, int *got_cycles);

/* during an execute() call end the execution */
extern void cpu_end_execute(int flag);

#endif
