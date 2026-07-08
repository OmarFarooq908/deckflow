---
id: pd-001
deck: Python::06 Pandas::Quick-Fire
type: recall
tags:
- python
- interview
- data-engineering
- pandas
- groupby
priority: normal
---

> Given DataFrame `df` with columns `region`, `product`, `revenue`,
> write one line to get **total revenue per region**.

---

```python
df.groupby("region")["revenue"].sum()
# or
df.groupby("region", as_index=False)["revenue"].sum()
```
