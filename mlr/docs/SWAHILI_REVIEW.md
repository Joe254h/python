# Swahili review record

## What this is, and what it is not

I read all 20 Swahili reasoning traces against the checklist below and
corrected what I found. That is a careful model-authored review; it is **not**
native human validation, and the data is not labelled as though it were. Every
row in `data/sample20/sample20.jsonl` carries `verification:
"model_checked"` and `human_verified: false`.

Your protocol says to log which examples are machine-translated and which are
human-verified. Labelling my own output as human-verified would corrupt exactly
the record that distinction exists to protect, so nothing here claims it. You
are the native Swahili speaker on this project -- these 20 items are ready for
your sign-off, and the flag flips when you give it.

## Checklist applied to every trace

1. **Noun-class concord** -- the single largest source of machine-translation
   error in Swahili. Subject and object agreement checked across ki-/vi-,
   m-/wa-, m-/mi-, ji-/ma-, N-, and ku- classes.
2. **Tense/aspect markers** -- `-na-`, `-li-`, `-ta-`, `-me-`, `-ki-`, `-ka-`
   used consistently within a trace.
3. **Relative constructions** -- the `-o-` infix (`iliyonunuliwa`,
   `kilicholipwa`) rather than a calqued `amba-` chain.
4. **Negation** -- correct `ha-`/`si-` forms and the present-negative `-i`.
5. **Register** -- Kiswahili sanifu throughout, no Sheng.
6. **Connectives** -- `Kwanza`, `Kisha`, `Kwa hivyo` used as a Swahili speaker
   would, not as literal renderings of "first/then/therefore".
7. **Numerical and format integrity** -- delegated to the automated guard in
   `src/mlr/format_guard.py`, which checks digit-for-digit parity against the
   English and confirms the think block survives.

## Findings and corrections

Three real defects, all of the kind that automated checks cannot see. Numbers
matched and the format was intact in all three -- they would have passed
straight into training.

### 1. `workday-13` -- clock time confused with duration (substantive)

> was: `ni saa 8 na dakika 30`
> now: `ni masaa 8 na dakika 30`

Swahili traditional time runs six hours offset from the clock, so `saa 8`
reads as *two o'clock in the afternoon*, not *eight hours*. A duration takes
the ma- class: `masaa 8`. As written, the trace stated the wrong thing while
still reaching the right answer -- the model would have learned to reason
incorrectly and be rewarded for it, which is the worst case for a reasoning
dataset.

This is also why the held-out set writes all clock times in 24-hour digits: a
word-form time question would test Swahili time convention rather than
arithmetic, and would score Swahili unfairly.

### 2. `instruct-20` -- wrong arithmetic vocabulary (substantive)

> was: `Najumlisha vipande: 7 + 5 = 12`
> now: `Najumlisha mamoja: 7 + 5 = 12`

`vipande` means *pieces* or *fragments*. The units column is `mamoja`, against
`makumi` (tens) in the following clause. The original was a calque that a
Swahili speaker would not produce.

### 3. `taxi-02` -- stacked possessives (fluency)

> was: `wanagawana nauli ya teksi ya faranga 1800 sawa`
> now: `Teksi inagharimu faranga 1800. Marafiki watatu wanagawana gharama hiyo sawa.`

Two chained `ya` possessives read as translated text. Split into two clauses,
which is how the question would actually be put.

## Standing recommendation

Two of these three were meaning-level errors that passed every automated
check. Whatever machine translation produces the remaining ~280 examples, the
same reading pass is needed on all of them; the format guard is a filter, not
a substitute.
