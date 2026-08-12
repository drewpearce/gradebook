---
status: accepted
---

# Grade computation: blanks excluded, empty category means Incomplete

A Category's percentage is computed only over the Assignments a Student has
actually been **scored** on (within their Audience): unscored applicable
Assignments are excluded from both numerator and denominator, not treated as
zero. A Subject Grade is shown as **Incomplete** whenever any weighted Category
has no scored applicable Assignment for that Student; only once every weighted
Category has content is a numeric Grade + Letter Grade produced. Because
completeness requires every Category to be present, the weights always sum to
100% at that point and no re-scaling is applied.

## Considered options

- **Missing = zero.** Rejected: in an early-elementary class a blank usually means
  "not entered / not yet due," and zero-filling would make a grade swing wildly
  and misleadingly mid-term.
- **Re-scale remaining categories when one is empty.** Rejected: silently
  inflating a single category's weight to 100% hides that the grade is based on a
  fraction of the intended work; "Incomplete" is the more honest signal.
- **Blanks excluded + Incomplete on empty category (chosen).** A grade is only
  shown when it is trustworthy, and a blank never hurts a Student.

## Consequences

- Grade computation is a pure function of (a Student's Scores, their Audience, the
  Subject's Categories/weights) returning either a numeric Grade or Incomplete.
- The UI must render "Incomplete" as a first-class Grade state, and ideally show
  *which* Category is empty so the teacher knows what to enter.
- If a teacher wants a missing assignment to actually count as zero, that is an
  explicit Score of 0, not a blank — a distinction the score-entry UI must make
  clear.
- **Weights that don't sum to 100 are handled softly, not enforced at write.** The
  pure module (`app/domain/grades.py`) assumes the weighted Categories sum to 100
  and normalizes otherwise; the API layer (`app/services/grades.py`) does *not*
  reject a Category edit that leaves the total ≠ 100 — it surfaces the shortfall as
  a second **Incomplete** reason (`weights_not_100`) at grade time. This is a
  deliberate extension of Incomplete beyond the empty-Category case above, chosen
  so a Teacher can build a Subject's Categories incrementally (progressive
  disclosure) without mid-setup errors. The trade-off: a mis-weighted Subject reads
  as Incomplete rather than being blocked on save.
