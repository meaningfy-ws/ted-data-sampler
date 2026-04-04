# Pass 2 — Gap Filler Algorithm

## Overview

The Gap Filler algorithm is the second pass of a two-pass sampling strategy for generating test data for eForms mapping projects. It takes as input a list of missing/uncovered XPath entries (identified by the Mapping Workbench) and a pool of notice XML files, then finds the minimum set of notices that satisfy all those XPaths.

## Problem Context

The first pass (Pass 1) uses basic structural XPaths to achieve coverage, but these lack SDK predicates and conditions. The Gap Filler addresses this by using **real XPath execution** against XML content to verify both:
1. The element exists at the given XPath
2. Any business conditions are satisfied

## Input

| File | Format | Description |
|------|--------|-------------|
| Missing XPaths | JSON | List of `MissingXPathEntry` objects with `absolute_xpath`, `xpath_condition`, `iterator_xpath`, etc. |
| Notice List | Text | One absolute file path per line to XML notice files |
| (Optional) Exclude List | Text | Notice paths already selected in Pass 1 to exclude |

## Output

| File | Description |
|------|-------------|
| `result_notices.txt` | Selected notice file paths (one per line) |
| `remaining_uncovered.txt` | Entry IDs that could not be covered |
| `coverage_report.json` | Detailed JSON with coverage mapping and summary |
| `logs.log` | Runtime log messages |

## Algorithm Steps

### Step 1: Sort the Entry Pool

Entries are sorted by:
- **Primary**: Iterator XPath length (descending) — deeper/more specific nodes are harder to cover, process them first
- **Secondary**: Absolute XPath length (ascending) — simpler paths are easier, try them first as fallback

```python
pool = sorted(entries, key=lambda e: (-len(e.iterator_xpath), len(e.absolute_xpath)))
```

### Step 2: Candidate Discovery (Fast Text Scan)

For each notice file:
1. Read the entire file as raw text (no XML parsing)
2. For each entry, check if all segments of `abs_xpath_reduced` appear in the text
3. If all segments found, add notice to entry's candidate list

This is a loose pre-filter — false positives are expected. Real validation happens in Step 4.

```
Time complexity: O(N × E × S) where N=notices, E=entries, S=avg segments per XPath
```

### Step 3: Cross-Coverage Analysis

Build a reverse index mapping each candidate notice to the entries it could cover:

```
notice_to_entries: {
  "/path/to/not1.xml": ["BT-27", "BT-28", "ND-1"],
  "/path/to/not2.xml": ["BT-27", "BT-29"],
  ...
}
```

Then sort each entry's candidate list by coverage count (descending):

```
sorted_candidates["BT-27"] = [not1.xml (covers 3), not2.xml (covers 2), ...]
```

This ensures notices that could cover multiple entries are tried first — greedy optimization.

### Step 4: Greedy Selection with Two-Stage Validation

For each entry (in sorted order):
1. Try each candidate notice (in sorted order)
2. Validate using two-stage XPath checking (see below)
3. If valid:
   - Add notice to result
   - Check all other entries this notice could cover (using `notice_to_entries`)
   - If any are also satisfied, mark them as covered too
   - Remove covered entries from the pool
4. Continue until all entries covered or candidates exhausted

### Step 5: Two-Stage XPath Validation

**Stage A — Absolute XPath Check:**
```python
result = validator.check_xpath_expression(entry.absolute_xpath)
if result is None or result.size == 0:
    return False  # Element not found
```

**Stage B — Condition Check (if condition exists):**
```python
iterator_result = validator.check_xpath_expression(entry.iterator_xpath)
for each iterator_node in iterator_result:
    validator.xpp.set_context(xdm_item=iterator_node)
    cond_result = validator.check_xpath_expression(entry.xpath_condition)
    if cond_result is true:
        return True  # Condition satisfied
return False
```

Why two stages? The `absolute_xpath` contains structural predicates (navigation), while `xpath_condition` contains business rules that must be evaluated against the iterator context.

## Complexity Analysis

| Phase | Complexity |
|-------|-------------|
| Candidate Discovery | O(N × E × S) |
| Cross-Cverage Build | O(C log C) where C = total candidate relationships |
| Greedy Selection | O(E × C_max × (P + X)) |

Where:
- N = number of notice files
- E = number of missing entries
- S = average segments per reduced XPath
- C = total candidate relationships
- C_max = maximum candidates per entry (≤ N)
- P = XML parsing time
- X = XPath evaluation time

**Practical notes:**
- Early termination reduces actual runtime significantly
- Cross-coverage bonus: when a notice is selected, it automatically checks other entries
- Each notice is parsed once and immediately closed (no caching to avoid slow cleanup)

## Design Decisions

| Decision | Rationale |
|----------|------------|
| Raw text pre-filter | Avoids expensive XML parsing for millions of notices |
| Iterator as context | Condition references sibling elements, not the field itself |
| No XML caching | Saxon's `close()` is slow; parse-validate-close per notice is faster overall |
| Sort by iterator depth | Hard-to-cover entries processed first to avoid "easy" notices consuming their only candidates |