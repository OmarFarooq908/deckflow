---
id: pd-002
deck: Python::06 Pandas::Quick-Fire
type: mental-model
tags:
- python
- interview
- data-engineering
- pandas
- join
priority: normal
---

> When do you use `merge` vs `join` in pandas?

---

```
merge — general SQL-style joins on columns; explicit left/right keys.

join — convenience wrapper; joins on index by default.

Prefer merge for clarity in interviews unless index join is intentional.
```

```python
pd.merge(df1, df2, on="key", how="left")
df1.join(df2, how="inner")
```
