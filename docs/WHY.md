# Why it's built this way

## The problem

A recall-by-genotype study invites people back because of their genotype, so selection has to be
fair, reproducible and blind to the people doing the inviting. Doing it by spreadsheet makes it easy
to bias groups by accident and hard to show how a list was produced.

## Design choices

**Why spread selection across the age range?** Because the first version took the youngest people
in every group while the README called it balancing. Even spacing over the age-sorted pool keeps
each group's age profile close to the eligible pool and is easy to explain.

**Why balance on sex before age?** Because sex affects many phenotypes, and an unbalanced group can
create a difference that is not genetic. Splitting slots across sexes first is transparent; if one
sex is short, the other fills the gap and the summary shows it.

**Why deterministic rather than random?** Because a design should be reproducible from its inputs
for audit. Randomness adds little when the rule is "even spacing", and a fixed tie-break by ID
removes ambiguity.

**Why report shortfall instead of filling the group?** Because relaxing age limits or consent rules
to hit a number is a scientific and ethical decision, not a coding one.

**Why a blinded export?** Because invitation staff should not know participants' genotypes. A list
sorted by group leaks the group even without a group column, so the blinded list is sorted by ID.

## Questions worth asking

**"Your groups are balanced internally, but are they comparable to each other?"**
Not guaranteed. If the e4/e4 pool is older than the e3/e3 pool, the selected groups will be too.
Frequency matching across groups is the next step; until then the design reports age range and sex
counts per group so the difference is visible.

**"What about ancestry?"**
Genotype frequencies differ by ancestry, so a genotype-based comparison can pick up ancestry
differences instead. This tool does not model ancestry, and the README says so. A real design would
restrict or stratify by genetic ancestry, which needs principal components, not a self-reported
field.

**"How do you know the right people were excluded?"**
Each exclusion stage is named and counted, and stages run in a fixed order, so the counts can be
checked against the source data. The eligible records, not just their IDs, pass to the designer, so
nothing is re-looked-up and mismatched.

## What's next

- Frequency matching across groups on age band and sex.
- Over-recruitment per group with a ranked reserve list.
- A CLI that writes the blinded list, restricted key and protocol in one step.
