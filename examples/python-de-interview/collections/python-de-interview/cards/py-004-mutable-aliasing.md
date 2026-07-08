---
id: py-004
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
priority: high
links:
- lc347
---

```python
a = [1, 2]
b = a
b.append(3)
print(a)
```

---

```python
[1, 2, 3]
```
Both variables reference the **same list** (mutable aliasing).
