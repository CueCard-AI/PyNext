# Phase 17 Backup (Pre-Unified Redesign)

This file contains the original Phase 17 content before the unified reactive system redesign.
Kept for reference. This content was replaced on the unified redesign.

---

#### Phase 17: SolidJS-Like Reactive System (Build-Time Compiled)

**Status:** Planned  
**Priority:** P0 (Critical)  
**Target Tests:** 1,000+

This phase represents a complete rebuild of PyNext's client-side reactivity to achieve true SolidJS-level performance through **build-time compilation**. This is a clean break from the current runtime-based approach.

**Why This Phase Is Critical:**

The current PyNext reactivity system has fundamental limitations:

| Gap | Current State | Impact |
|-----|---------------|--------|
| List reconciliation | Server-rendered only | Lists don't update client-side |
| Conditional rendering | No Show/When | Can't toggle visibility reactively |
| Python-to-JS compilation | Runtime regex hacks | Unreliable, slow, limited patterns |
| Event handler transpilation | Spy mechanism workarounds | Only simple Signal ops work |
| Component lifecycle | Basic/incomplete | No proper mount/cleanup |
| Form binding | Missing | No two-way input binding |
| Client-side routing | Missing | Full page reloads required |
| DevTools | None | No debugging support |

[... rest of original Phase 17 content preserved in git history ...]

