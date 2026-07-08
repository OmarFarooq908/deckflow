---
deckflow: 1
id: python-de-interview
title: Python Data Engineering Interview
description: |
  Comprehensive spaced-repetition deck for Python fundamentals, interview patterns,
  pandas quick-fire, and LeetCode ↔ data-engineering mappings.

  Organized for daily review: fundamentals first, patterns second, domain mappings third.
author: dev
version: 1.0.0
created: 2026-07-08
updated: 2026-07-08
tags: [python, interview, data-engineering]
config:
  new_per_day: 20
  max_reviews_per_day: 150
  desired_retention: 0.9
  review_order: deck
  bury_related: false
sources:
  - label: LeetCode practice repo
    path: ../../LeetCode
  - label: DE study notes
    path: ./notes
---

# Python Data Engineering Interview

> **How to use this deck**
>
> 1. Import into Deckflow: `deckflow import examples/legacy/advanced_sample_deck.md`
> 2. Review 20 new cards/day (collection default) — adjust per subdeck via `**Deck config:**`
> 3. Use `**Links:**` to jump to LeetCode problems after a Good/Easy rating
> 4. Suspended cards (`status: suspended`) stay in git but skip the queue

This file demonstrates **Deckflow Markdown v1**. See [`docs/DECK_FORMAT.md`](../docs/DECK_FORMAT.md) for the full specification.

---

## Deck: Python::01 Fundamentals::Variables & Types

**Deck description:** Core types, mutability, identity (`is` vs `==`), and truthiness. Master this before patterns.
**Deck tags:** `syntax` `fundamentals`
**Deck config:**
```yaml
new_per_day: 10
inherit_tags: true
```

### Card: py-001-immutable-types

**Card id:** `py-001`
**Type:** recognition
**Concepts:** `python::fundamentals` `types::mutability`
**Tags:** `immutable` `recognition`
**Difficulty:** 2
**Objective:** Name all immutable built-in types from memory in an interview.
**Priority:** high
**Status:** active
**Links:** `url:https://docs.python.org/3/library/stdtypes.html`
**Source:** Python docs — Built-in Types

**Front:**
> Which Python types are **immutable**?

**Back:**
```
int, float, bool, str, tuple, frozenset
```

---

### Card: py-002-mutable-types

**Card id:** `py-002`
**Type:** recognition
**Concepts:** `python::fundamentals` `types::mutability`
**Tags:** `mutable` `recognition`
**Prerequisites:** `py-001`
**Difficulty:** 2
**Objective:** Contrast mutable types against immutable types quickly.
**Priority:** high
**Status:** active
**Card config:**
```yaml
related: [py-001-immutable-types]
```

**Front:**
> Which Python types are **mutable**?

**Back:**
```
list, dict, set, bytearray
```

---

### Card: py-003-none-identity

**Card id:** `py-003`
**Type:** mental-model
**Tags:** `mental-model` `pitfall`
**Priority:** normal
**Status:** active
**Hint:** `None` is a singleton — how do you test for it?

**Front:**
> What does `None` represent in Python? How should you test for it?

**Back:**
```
A singleton meaning "no value" / absence of value.

Not the same as 0, False, or "".

Always use:  x is None   (not x == None)
```

---

### Card: py-004-mutable-aliasing

**Card id:** `py-004`
**Type:** pitfall
**Tags:** `pitfall` `output`
**Priority:** high
**Status:** active
**Links:** `lc347`

**Front:**
```python
a = [1, 2]
b = a
b.append(3)
print(a)
```

**Back:**
```python
[1, 2, 3]
```
Both variables reference the **same list** (mutable aliasing).

---

### Card: py-005-tuple-immutability

**Card id:** `py-005`
**Type:** pitfall
**Tags:** `pitfall` `output`
**Priority:** normal
**Status:** active

**Front:**
```python
a = (1, 2)
b = a
# Can you do b[0] = 5?
```

**Back:**
```
No. Tuples are immutable → TypeError on item assignment.
```

**Notes:** A tuple containing a list IS immutable as a tuple, but the nested list can still be mutated.

---

## Deck: Python::01 Fundamentals::Operators

**Deck description:** Arithmetic, membership, unpacking, and Pythonic idioms.
**Deck tags:** `syntax`
**Deck config:**
```yaml
new_per_day: 8
```

### Card: py-006-division-operators

**Card id:** `py-006`
**Type:** recognition
**Tags:** `syntax`
**Priority:** normal
**Status:** active

**Front:**
> Integer division vs float division in Python 3?

**Back:**
```python
7 / 2   # 3.5  — true division (float)
7 // 2  # 3    — floor division
7 % 2   # 1    — modulo
2 ** 3  # 8    — exponent
```

---

### Card: py-007-unpacking-star

**Card id:** `py-007`
**Type:** recognition
**Tags:** `syntax` `pattern`
**Priority:** normal
**Status:** active

**Front:**
> Explain unpacking with `*` in assignment.

**Back:**
```python
first, *rest = [1, 2, 3, 4]
# first=1, rest=[2, 3, 4]

a, *mid, b = [1, 2, 3, 4]
# a=1, mid=[2, 3], b=4
```

---

## Deck: Python::07 Interview Patterns::Top-K

**Deck description:** Heap / quickselect patterns mapped to real problems.
**Deck tags:** `pattern` `heap`
**Deck config:**
```yaml
new_per_day: 5
```

### Card: lc-347-top-k-pattern

**Card id:** `lc-347`
**Type:** pattern
**Concepts:** `pattern::heap` `python::algorithms`
**Tags:** `pattern` `heap` `mapping`
**Difficulty:** 4
**Objective:** Recognize Top-K problems and cite heap complexity without hesitation.
**Priority:** high
**Status:** active
**Links:** `lc347` `file:../../LeetCode/lc347.py` `url:https://leetcode.com/problems/top-k-frequent-elements/`
**Source:** LeetCode 347 — Top K Frequent Elements

**Front:**
> **Pattern:** Need Top-K frequent / largest / smallest elements.
>
> What data structure and complexity?

**Back:**
```
Use a min-heap of size K (for top-K largest).

Build frequency map O(n), heapify O(n log k).

Overall: O(n log k) time, O(n) space.

Python: heapq.nlargest(k, items, key=...)
```

**Notes:** For K close to n, quickselect O(n) average may win. For streaming data, use fixed-size heap.

---

### Card: lc-347-top-k-stub

**Card id:** `lc-347-code`
**Type:** recall
**Tags:** `pattern` `heap` `recall`
**Priority:** high
**Status:** suspended
**Links:** `lc347`
**Source:** LeetCode 347

**Front:**
> Write the heap-based Top-K frequent elements solution (function signature only, then implement).

**Back:**
```python
from collections import Counter
import heapq

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    return heapq.nlargest(k, counts.keys(), key=counts.get)
```

**Notes:** Suspended until fundamentals deck retention > 85%. Remove `status: suspended` to activate.

---

## Deck: Python::06 Pandas::Quick-Fire

**Deck description:** High-frequency pandas interview questions. Review after fundamentals.
**Deck tags:** `pandas`
**Deck config:**
```yaml
new_per_day: 5
inherit_tags: true
```

### Card: pd-001-groupby-agg

**Card id:** `pd-001`
**Type:** recall
**Tags:** `pandas` `groupby`
**Priority:** normal
**Status:** active

**Front:**
> Given DataFrame `df` with columns `region`, `product`, `revenue`,
> write one line to get **total revenue per region**.

**Back:**
```python
df.groupby("region")["revenue"].sum()
# or
df.groupby("region", as_index=False)["revenue"].sum()
```

---

### Card: pd-002-merge-vs-join

**Card id:** `pd-002`
**Type:** mental-model
**Tags:** `pandas` `join`
**Priority:** normal
**Status:** active

**Front:**
> When do you use `merge` vs `join` in pandas?

**Back:**
```
merge — general SQL-style joins on columns; explicit left/right keys.

join — convenience wrapper; joins on index by default.

Prefer merge for clarity in interviews unless index join is intentional.
```

**Extra:**
```python
pd.merge(df1, df2, on="key", how="left")
df1.join(df2, how="inner")
```

---

## Deck: Meta::Study Plan

**Deck description:** Non-review reference cards — scheduling hints and milestones.
**Deck tags:** `meta`
**Deck config:**
```yaml
new_per_day: 0
```

### Card: meta-review-order

**Card id:** `meta-001`
**Type:** mental-model
**Tags:** `meta` `study-plan`
**Priority:** low
**Status:** suspended

**Front:**
> Recommended study order for this collection?

**Back:**
```
1. Python::01 Fundamentals (all subdecks)
2. Python::07 Interview Patterns
3. Python::06 Pandas
4. LeetCode ↔ DE mappings

Rule: 20 new/day collection default; drop to 10 if retention < 80%.
```

**Notes:** Reference card — keep suspended; not meant for daily review queue.
