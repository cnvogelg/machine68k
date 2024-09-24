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
#define CPU_END_MAX_CYCLES              0x0001
#define CPU_END_USER                    0x0002
#define CPU_END_TRAP_DEFER              0x0004
/* errors */
#define CPU_END_TRAP_ERROR              0x0010
#define CPU_END_PC_CHANGED_FUNC_ERROR   0x0020
#define CPU_END_RESET_INSTR_FUNC_ERROR  0x0040
#define CPU_END_INSTR_HOOK_FUNC_ERROR   0x0080
#define CPU_END_MEM_TRACE_FUNC_ERROR    0x0100
#define CPU_END_MEM_INVALID_FUNC_ERROR  0x0200
#define CPU_END_MEM_READ_FUNC_ERROR     0x0400
#define CPU_END_MEM_WRITE_FUNC_ERROR    0x0800

#define CPU_END_RECURSE_EXECUTE         0x1000
#define CPU_END_ERROR_MASK              0xfff0

/* used by mem or trap internally only! */
extern void cpu_end(int flag);

extern int cpu_execute(int max_cycles, int *got_cycles);

#endif
