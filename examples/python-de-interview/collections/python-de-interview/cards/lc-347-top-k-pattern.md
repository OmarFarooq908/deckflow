---
id: lc-347
deck: Python::07 Interview Patterns::Top-K
type: pattern
concepts:
- pattern::heap
- python::algorithms
tags:
- python
- interview
- data-engineering
- pattern
- heap
- mapping
difficulty: 4
objective: Recognize Top-K problems and cite heap complexity without hesitation.
priority: high
links:
- lc347
- file:../../LeetCode/lc347.py
- url:https://leetcode.com/problems/top-k-frequent-elements/
notes: For K close to n, quickselect O(n) average may win. For streaming data, use
  fixed-size heap.
source: LeetCode 347 — Top K Frequent Elements
---

> **Pattern:** Need Top-K frequent / largest / smallest elements.
>
> What data structure and complexity?

---

```
Use a min-heap of size K (for top-K largest).

Build frequency map O(n), heapify O(n log k).

Overall: O(n log k) time, O(n) space.

Python: heapq.nlargest(k, items, key=...)
```
