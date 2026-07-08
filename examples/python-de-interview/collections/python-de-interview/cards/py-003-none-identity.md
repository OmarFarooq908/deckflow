---
id: py-003
deck: Python::01 Fundamentals::Variables & Types
type: mental-model
tags:
- python
- interview
- data-engineering
- syntax
- fundamentals
- mental-model
- pitfall
priority: normal
hint: '`None` is a singleton — how do you test for it?'
---

> What does `None` represent in Python? How should you test for it?

---

```
A singleton meaning "no value" / absence of value.

Not the same as 0, False, or "".

Always use:  x is None   (not x == None)
```
