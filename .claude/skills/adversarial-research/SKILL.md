---
name: adversarial-research
description: >
  Adversarial extension of the autoresearch loop. Adds two adversarial modes on top of the base
  autoresearch skill: (A) Generator-vs-Critic at the meta-level — a critic agent vets every
  hypothesis BEFORE it runs, rejecting duplicates, unrealistic claims, and broken patches; and
  (B) Adversarial-Task — two competing metrics inside one experiment (e.g. GAN-style primary +
  adversary), with a watcher that detects collapse when one side dominates. Modes can be
  combined (mode A on top of mode B = full adversarial-research). Use this skill whenever the
  user wants: critic-gated hypothesis generation, GAN-like adversarial training loops, two-metric
  experiments, balance monitoring, or "adversarial" anything in the context of autoresearch.
  Trigger on phrases like "adversarial research", "состязательный авторесерч", "generator vs critic",
  "gvc loop", "adversarial training loop", "adversarial task", "adversarial loop", "критик
  гипотез", "две метрики", "баланс GAN".
---

# Adversarial Research

This skill **extends** the base `autoresearch` skill with adversarial dynamics. Before reading further, ensure you understand the base skill's conventions — they are inherited verbatim:

- Metric format: `METRIC: <name>=<value>` on the last line(s) of stdout
- State file: `autoresearch_config.json` (this skill **adds** fields, never replaces base ones)
- Log file: `experiment_log.md` (extended with new fields per mode)
- Hypothesis file: `research_directions.md` with `- [ ]` / `- [x]` checkboxes
- Git workflow: commit on improvement, `git checkout -- .` on regression, no new branches, no `push`, no `reset --hard`
- Hard cap on `max_iterations`, working tree must be clean before edits, never delete files without explicit user request
- Bilingual: detect language from the first user message and reply in that language

If a convention is not mentioned here, **inherit it from `autoresearch/SKILL.md` — do not redefine.**

---

## Step 0: Detect mode and context

Detect the user's language. Respond in that language throughout.

Read `autoresearch_config.json` if it exists:

| Situation | What to do |
|---|---|
| File does not exist | Run [Onboarding](#onboarding) — ask all base questions plus mode |
| File exists, has `mode` field | Skip to [Research Loop](#research-loop) for that mode |
| File exists, no `mode` field (base autoresearch) | Run [Upgrade Path](#upgrade-path) — preserve everything, ask user for mode, write it back |

The `mode` field is the entry point to all behavior in this skill. Three valid values:
- `"adversarial-gvc"` — Generator vs Critic at meta-level (mode A)
- `"adversarial-task"` — two competing metrics inside one experiment (mode B)
- `"adversarial-gvc+task"` — both, layered (critic vets hypotheses for a two-metric run)

---

## Onboarding

Ask all questions from the base skill (codebase, run command, research directions), **plus** one extra question — adapt phrasing to the user's language:

> Which adversarial mode would you like?
>
> **A — Generator vs Critic** (meta-level): a critic agent reviews every hypothesis before the experiment runs, rejecting duplicates and unrealistic ideas. Useful for noisy hypothesis spaces or to slow down the loop with a quality gate.
>
> **B — Adversarial Task** (training-level): your `train.py` outputs two metrics (e.g. primary loss + adversary balance), the loop commits only when both are healthy. Useful for GAN-style training, fairness vs. accuracy tradeoffs, multi-objective work.
>
> **A+B — Both**: critic over a two-metric task. The full adversarial-research setup.

If the user picks B or A+B, also ask:
1. What are the two metric names?
2. Direction for each (`higher_is_better` / `lower_is_better`)?
3. Which one is `primary` (the optimization target) and which is `adversary` (the constraint)?

Write all this into `autoresearch_config.json` (see [Config schema](#config-schema)). Then ask for confirmation before starting the loop, just like the base skill.

---

## Upgrade Path

The user already has a base autoresearch project (`autoresearch_config.json` without `mode`). Do not break it.

1. Read the existing config — preserve `best_value`, `best_commit`, `iterations_run`, `metric_name`, `metric_direction`, `eval_command`, `max_iterations`.
2. Ask the user which mode to add (A / B / A+B). Explain the tradeoffs as in onboarding.
3. If B or A+B: ask the user to confirm or rename their existing metric as `primary`, then add the second metric. Adversary metric must already be present in `train.py` output, or offer to add it.
4. Write the upgraded config — base fields untouched, new fields added.
5. Append a marker entry to `experiment_log.md`:
   ```markdown
   ## Mode upgrade — YYYY-MM-DD HH:MM
   - Upgraded from base autoresearch to mode `<mode>`
   - Preserved best_value=<value>, iterations_run=<N>
   ```

Wait for explicit user confirmation before continuing into the loop.

---

## Config schema

The full extended `autoresearch_config.json`. Base fields appear first, mode-specific extensions after.

```json
{
  "project_path": ".",
  "eval_command": "python train.py --epochs 5 --seed 42",
  "iterations_run": 0,
  "max_iterations": 20,

  "mode": "adversarial-gvc+task",

  "metric_name": "fid",
  "metric_direction": "lower_is_better",
  "best_value": 42.31,
  "best_commit": "experiment: ...",

  "metrics": [
    {"name": "fid", "direction": "lower_is_better", "role": "primary"},
    {"name": "balance", "direction": "lower_is_better", "role": "adversary"}
  ],
  "best_adversary": 0.18,
  "scoring_formula": "commit_if_primary_improved_and_adversary_within_threshold",
  "adversary_threshold": 1.5,

  "critic_max_revisions": 2,
  "collapse_window": 3
}
```

**Field rules:**
- For mode A only: `metric_name`/`metric_direction`/`best_value` work as in base. `metrics` array is omitted or has length 1.
- For mode B or A+B: `metrics` is the source of truth. `metric_name`/`metric_direction`/`best_value` mirror the `primary` entry for backward compatibility with the base skill's parser.
- `best_adversary` exists only for B/A+B and tracks the adversary value at the commit that set `best_value`.
- `critic_max_revisions` defaults to 2. `collapse_window` defaults to 3.

---

## Research Loop — Mode A: Generator vs Critic

Each iteration adds a meta-stage **before** running the experiment.

### A.1 Read state

Read `autoresearch_config.json`, `research_directions.md`, `experiment_log.md`, current `train.py`. Pass them as context to the Generator (see `prompts/generator.md`).

### A.2 Generator proposes

Generator output must contain:
- A hypothesis sentence (matches what would go into `research_directions.md`)
- A concrete patch (unified diff or precise edit instructions for `train.py`)
- Expected effect (what metric movement is plausible and why)

If the next hypothesis is already in `research_directions.md` as `- [ ]`, take it as the seed; otherwise generate a new one.

### A.3 Critic vets

Pass the Generator's full output to the Critic (see `prompts/critic.md`). Critic returns one of three verdicts:

- **APPROVE** — proceed to A.4 (run experiment).
- **REVISE** — Generator gets the critic's notes and tries again. Hard cap: `critic_max_revisions` (default 2). Track revision count in memory for this iteration.
- **REJECT** — log the rejected hypothesis to `experiment_log.md` (see template in `templates/experiment_log_entry.md`) with the critic's reason. **Do not run the experiment.** Mark the hypothesis as `- [x] (rejected by critic)` in `research_directions.md`. Move to next hypothesis.

Logging rejections is critical — it shapes future Generator output and prevents looping on the same bad ideas.

### A.4 Run experiment

Same as base skill: clean tree check → apply patch → run `eval_command` → parse `METRIC:` line.

### A.5 Decide and commit

Use `metric_direction` (mode A operates on a single metric, like the base skill).

- Improvement → `git commit` with message `experiment: <hypothesis> → <metric>=<new> (was <old>) [critic: APPROVE]`.
- Regression → `git checkout -- .`.

Update `experiment_log.md` using the mode-A template — include the `Critic verdict` field so we can see how often the critic was right.

### A.6 Feedback to roles (lightweight)

After the outcome is known, retain a short note in memory for the next iteration's prompts:
- If outcome was ✅ Improvement → mention this hypothesis as a positive example to Generator.
- If outcome was ❌ Regression and critic had said APPROVE → mention to Critic that it missed something. Do not re-prompt or re-train; just include the note in next iteration's context.

This is "feedback" only in the sense of in-context examples — there is no real training going on.

---

## Research Loop — Mode B: Adversarial Task

The hypothesis-generation logic is the base skill's. The novelty is **two metrics** parsed from stdout and a balance watcher.

### B.1 Read state, including both metrics

Both `primary` and `adversary` values are tracked. The script must emit two `METRIC:` lines:

```
METRIC: fid=42.31
METRIC: balance=0.18
```

Parser: scan stdout for **all** lines matching `METRIC: <name>=<value>`. Match each against `metrics` array in config. Both must be present and parseable, otherwise treat as failure (revert).

### B.2 Pick hypothesis with tag

In mode B, hypotheses in `research_directions.md` carry a tag at the start:

```markdown
- [ ] [primary] Try learning rate 1e-4 (smaller LR for generator)
- [ ] [adversary] Add label smoothing 0.1 to discriminator
- [ ] [both] Try gradient penalty (affects both)
```

Tags are advisory — they help the user (and a wrapping Generator if mode is A+B) see what is being targeted. Take the first unchecked item regardless of tag.

### B.3 Run experiment, parse two metrics

Same as base, but parser collects both. If only one metric line appears, it's an error — revert and log.

### B.4 Decide via scoring formula

Default formula `commit_if_primary_improved_and_adversary_within_threshold`:

```
new_primary IMPROVED over best_primary  (using primary's direction)
AND
new_adversary is within adversary_threshold * best_adversary
  (for lower_is_better: new <= threshold * best)
  (for higher_is_better: new >= best / threshold)
```

If both conditions hold → commit, update `best_value` (primary) and `best_adversary`.
If primary improved but adversary degraded past the threshold → revert. Log as `⚠️ Primary improved, adversary degraded → revert`.
If primary regressed → revert.

The user can override `scoring_formula` in the config. Recognize at minimum:
- `commit_if_primary_improved_and_adversary_within_threshold` (default)
- `commit_if_pareto_improvement` — both metrics must improve, no threshold
- `commit_if_weighted_sum_improved` — requires `weights` field; commit if `w_primary * primary + w_adversary * adversary` improves (in primary's direction)

If the formula is unrecognized, ask the user — do not silently fall back.

### B.5 Watch for collapse

After updating the log, check the last `collapse_window` (default 3) iterations. If for `collapse_window` consecutive iterations:
- only one metric is moving (the other is flat within ±1%) — that side is winning unilaterally, or
- one metric is consistently improving while the other consistently degrades

Then trigger `prompts/balance_watcher.md`. Watcher inspects the recent log entries and proposes 1–3 balance hypotheses (lr ratio change, update frequency, label smoothing, gradient clipping). It prepends these to `research_directions.md` with `[both] [priority]` tags so they run next.

Do not silently auto-correct training — the watcher only adds hypotheses; the loop tries them in order like any others.

---

## Research Loop — Mode A+B: Combined

Generator-vs-Critic over a two-metric task. Both mechanisms apply:

1. Generator proposes (A.2), aware of `metrics` array and tags hypotheses accordingly (`[primary]` / `[adversary]` / `[both]`).
2. Critic vets with extra checks: does the patch actually target what the tag claims? Does it risk collapsing one side?
3. Run, parse two metrics (B.3), decide via scoring formula (B.4).
4. Update log with **both** `Critic verdict` and `both_metrics` fields.
5. Watch for collapse (B.5) — if triggered, the watcher's hypotheses go through Generator/Critic on subsequent iterations like everything else.

---

## Metric output format (mode B and A+B)

`train.py` must emit two lines, in any order, each matching `METRIC: <name>=<value>` exactly:

```
METRIC: fid=42.31
METRIC: balance=0.18
```

If the user's script emits only one metric, offer to add the second print statement. Do not invent values — ask the user where the second metric comes from.

---

## Templates and prompts

This skill loads supporting files at runtime. Read them when the relevant phase fires:

- `prompts/generator.md` — Generator role system prompt (mode A and A+B)
- `prompts/critic.md` — Critic role system prompt (mode A and A+B)
- `prompts/balance_watcher.md` — Balance watcher prompt (mode B and A+B)
- `templates/research_directions_gvc.md` — initial hypothesis file for mode A scaffolding
- `templates/research_directions_task.md` — initial hypothesis file for mode B/A+B scaffolding (with tags)
- `templates/experiment_log_entry.md` — extended log entry templates per mode

Keep prompt and template files small and focused. Edit them without changing this SKILL.md.

---

## Safety rules (inherited from base, do not weaken)

- Never `git push` — only local commits.
- Never `git reset --hard`, `git push --force`, no `--no-verify`.
- Always verify `git status` is clean before applying a patch.
- If the tree is dirty at loop start, pause and ask the user.
- Never delete files unless the user explicitly asks.
- Hard limit: `max_iterations` (default 20). The loop must stop there.
- Critic cannot bypass the `max_iterations` cap by retrying — REVISE counts toward the count only if it leads to a run.
- Watcher cannot trigger more than once per iteration; its hypotheses go through the normal queue.
