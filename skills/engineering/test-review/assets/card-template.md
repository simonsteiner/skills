<!--
  test-review candidate card. Copy to docs/test-review/YYYY-MM-DD-<slug>/C<n>-<card-slug>.md, one per candidate.
  Keep the block for the card's kind (Blind spot, Waste, or Infra) and delete the other two.
  Keep the badge emoji. Stay under the project's token budget (5,000 tokens = 20 KB without one).
  Delete this comment.
-->

# C1 · <title>

[← Report](README.md)

<🕳️ blind spot | 🗑️ waste | 🔧 infra> · 🟢 **Strong** · 🔴 **live defect** · <↔ `two-way` | 🚪 `one-way`> · fix: <`tdd` | `prune-tests` | `direct`> · builds on: <— | C3>

`<src/billing/invoice.py:40-118>` · `<tests/test_billing.py:12>`

<one line with the count or timing that makes the case, e.g. "14 commits in 6 months, 3 of them fixes (a1b2c3d, …), none touched a test">

> [!CAUTION]
> **Live defect:** <input> → <wrong output>, no error. <!-- only for a live defect -->

<!-- ===== Blind spot ===== -->

**Seams** (confirmed at Step 5):

| Seam | Catches | Misses |
|---|---|---|
| `<Invoice.issue(order)>` | <rounding, tax per line, empty order> | <PDF rendering> |

**Pin:**

| Behaviour | Where | Evidence |
|---|---|---|
| <totals round half-even per line> | `<src/billing/invoice.py:77>` | <fix a1b2c3d added no test> |
| <an order with no lines raises EmptyOrder> | `<src/billing/invoice.py:52>` | <guard never driven; uncovered> |

<!-- ===== Waste ===== -->

**Prune:**

| Test | Why | Still guarded by | Cost | Action |
|---|---|---|---|---|
| `<tests/test_orders.py:88>` | <the implementation: asserts repo.save call order> | `<tests/test_checkout.py:20>` | <changed in 4 refactor commits> | delete |
| `<tests/test_orders.py:140>` | <the implementation: private `_items`> | nothing — only guard of the item total | <—> | rewrite |

<!-- ===== Infra ===== -->

**Now:** <what runs, where, and what it costs>

**Change:** <the one change>

**Measure:** <number it should move> — now <value>, from `<command>`

<!-- ===== all kinds ===== -->

| Problem | Fix | Wins |
|---|---|---|
| <one sentence: what hurts> | <one sentence: what changes> | <regression in rounding fails CI><br><−41 s per CI run> |

> [!NOTE]
> ADR <0007>: <one line on how it bears> <!-- only when an ADR bears on it -->

**After:** <!-- filled at Ship: tests added/removed, the mutation that turned each new test red, the Measure's new value -->

<details>
<summary>Decisions</summary>

<!-- one line each -->
Q1 — <question> → <answer>, because <fact>.

</details>
