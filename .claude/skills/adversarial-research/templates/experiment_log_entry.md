# Experiment log entry templates

These are the exact formats appended to `experiment_log.md` after each iteration. Choose the template by mode.

---

## Mode A — Generator vs Critic

```markdown
## Iteration N — YYYY-MM-DD HH:MM
- **Hypothesis**: <generator's HYPOTHESIS line>
- **Critic verdict**: APPROVE
- **Code change**: <one-line description>
- **Result**: <metric_name>=<value>  |  Best so far: <best_value>
- **Outcome**: ✅ Improvement (+X.XX%) / ❌ Regression / ⚠️ Error: <message>
```

If the critic asked for revisions before approving:

```markdown
## Iteration N — YYYY-MM-DD HH:MM
- **Hypothesis**: <final hypothesis after revision>
- **Critic verdict**: REVISE (round 1: <reason>) → APPROVE
- **Code change**: <...>
- **Result**: <...>
- **Outcome**: <...>
```

If the critic rejected it (no run happened):

```markdown
## Iteration N — YYYY-MM-DD HH:MM
- **Hypothesis**: <generator's HYPOTHESIS line>
- **Critic verdict**: REJECT — <critic's one-sentence reason>
- **Code change**: (not applied)
- **Result**: (not run)
- **Outcome**: 🚫 Rejected before execution
```

---

## Mode B — Adversarial Task

```markdown
## Iteration N — YYYY-MM-DD HH:MM
- **Hypothesis**: [primary] <description>
- **Code change**: <one-line description>
- **Result**: <primary_name>=<value> (was <best_primary>) | <adversary_name>=<value> (was <best_adversary>)
- **Outcome**: ✅ Both improved / ✅ Primary improved, adversary within threshold / ⚠️ Primary improved, adversary degraded → revert / ❌ Primary regression
```

---

## Mode A+B — Combined

Includes both `Critic verdict` and the two-metric `Result`:

```markdown
## Iteration N — YYYY-MM-DD HH:MM
- **Hypothesis**: [adversary] <description>
- **Critic verdict**: APPROVE
- **Code change**: <one-line description>
- **Result**: <primary_name>=<value> (was <best_primary>) | <adversary_name>=<value> (was <best_adversary>)
- **Outcome**: ✅ / ⚠️ / ❌
```

If the watcher fired before this iteration, add a one-line note above the entry:

```markdown
> Balance watcher fired before this iteration: <one-sentence summary>. Watcher hypotheses prepended to research_directions.md.

## Iteration N — YYYY-MM-DD HH:MM
...
```
