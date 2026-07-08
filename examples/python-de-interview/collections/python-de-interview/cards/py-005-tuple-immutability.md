---
id: py-005
deck: Python::01 Fundamentals::Variables & Types
type: pitfall
tags:
- python
- interview
- data-engineering
- syntax
- fundamentals
- pitfall
- output
priority: normal
notes: A tuple containing a list IS immutable as a tuple, but the nested list can
  still be mutated.
---

```python
a = (1, 2)
b = a
# Can you do b[0] = 5?
```

---

```
No. Tuples are immutable → TypeError on item assignment.
```
