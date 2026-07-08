---
id: lc-347-code
deck: Python::07 Interview Patterns::Top-K
type: recall
tags:
- python
- interview
- data-engineering
- pattern
- heap
- recall
priority: high
status: suspended
links:
- lc347
notes: 'Suspended until fundamentals deck retention > 85%. Remove `status: suspended`
  to activate.'
source: LeetCode 347
---

> Write the heap-based Top-K frequent elements solution (function signature only, then implement).

---

```python
from collections import Counter
import heapq

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    return heapq.nlargest(k, counts.keys(), key=counts.get)
```
