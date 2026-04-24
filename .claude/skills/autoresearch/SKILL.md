---
name: autoresearch
description: >
  Autonomous ML experiment loop — automatically generates hypotheses, runs experiments,
  evaluates results, and commits only improvements. Inspired by Andrej Karpathy's AutoResearch
  project (March 2026). Use this skill whenever the user wants to: automate ML/AI experiments,
  run an overnight training optimization loop, conduct auto-research on a model, set up a
  self-improving experiment cycle, or systematically find training speedups. Also trigger when
  the user has no code yet — the skill scaffolds a complete starter pack from scratch. Trigger
  on phrases like "запустить авторесерч", "автоматические эксперименты", "optimize training",
  "experiment loop", "auto-research", "run experiments overnight", "autoresearch".
---

# AutoResearch

You are acting as an autonomous research engineer. Your job: generate hypotheses, run experiments, commit improvements, discard regressions — repeating until the user's model is measurably better.

---

## Step 0: Detect context

**Detect the user's language** from the conversation and respond in that language throughout.

Check if `autoresearch_config.json` exists in the current working directory:
- **If it exists** → skip to [Research Loop](#research-loop) (this is an ongoing session)
- **If it does not exist** → start with [Onboarding](#onboarding)

---

## Onboarding

Ask the user the following questions — you can group them into a single friendly message:

1. **Codebase**: Do you have a training script or ML repo? If yes, what's the path?
2. **Metric**: What are we optimizing? (e.g., val_loss, accuracy, training speed). Higher is better or lower is better?
3. **Run command**: What command runs one experiment and prints the metric? (e.g., `python train.py --epochs 3`)
4. **Research directions**: Any ideas on what to try? (e.g., "different optimizers", "learning rate schedules") — or should I generate starting hypotheses?

**If the user has nothing** (no code, no ideas, no repo) — offer to build a complete starter pack. Ask: PyTorch, TensorFlow, or plain NumPy?

---

## Scaffold Mode

When the user has no existing code, build a working starter pack from scratch.

### Directory structure to create

```
autoresearch_project/
├── train.py
├── research_directions.md
├── experiment_log.md
└── autoresearch_config.json   ← written after baseline run
```

### train.py requirements

Write a clean, self-contained training script:
- Simple model (2-layer MLP for classification by default; ask if they want something else)
- Synthetic dataset (use `sklearn.datasets.make_classification` if available, else numpy random)
- Accepts `--seed INT` for reproducibility
- Runs in under 60 seconds
- Prints the optimized metric on the **last line** in exactly this format:
  ```
  METRIC: <name>=<value>
  ```
  Example: `METRIC: val_loss=0.4231`

### research_directions.md template

```markdown
# Research Directions

## Active hypotheses
- [ ] Try learning rates: 1e-2, 1e-3, 1e-4
- [ ] Compare optimizers: Adam vs SGD vs RMSprop
- [ ] Add dropout (0.1, 0.3, 0.5)
- [ ] Vary batch size: 32, 64, 128
- [ ] Add batch normalization after hidden layers

## Completed
(none yet)
```

### Initialize git

```bash
git init autoresearch_project
cd autoresearch_project && git add . && git commit -m "initial: baseline training script"
```

### Run baseline

Run the eval command, parse the `METRIC:` line, save to `autoresearch_config.json`:

```json
{
  "project_path": ".",
  "eval_command": "python train.py --epochs 5 --seed 42",
  "metric_name": "val_loss",
  "metric_direction": "lower_is_better",
  "best_value": 0.4231,
  "best_commit": "initial baseline",
  "iterations_run": 0,
  "max_iterations": 20
}
```

Tell the user:
- What the baseline metric is
- What hypotheses are queued
- Ask for confirmation before starting the loop: "Ready to start? I'll run experiments autonomously and only keep improvements."

**Wait for explicit user confirmation before starting the loop.**

---

## Research Loop

Each iteration follows this exact sequence:

### 1. Read current state

Read `autoresearch_config.json`, `research_directions.md`, and `experiment_log.md`.

### 2. Check stopping conditions

Stop and summarize if any of these are true:
- `iterations_run >= max_iterations`
- All hypotheses are checked off and no new ones can be generated
- User previously said "stop"

When stopping, print a summary table of all improvements found.

### 3. Pick next hypothesis

Take the first unchecked item (`- [ ]`) from `research_directions.md`.

If all are checked: generate 3 new hypotheses based on what worked so far (build on successes, explore adjacent ideas), add them to the file, then pick the first new one.

### 4. Make a targeted code change

Apply the hypothesis as a **minimal, focused change** to the training script — one thing at a time. This is crucial: small changes are interpretable; large changes hide what actually works.

Before editing:
```bash
git stash list  # check for unexpected stashed changes
git status      # confirm clean working tree
```

If the tree is dirty (uncommitted changes exist), warn the user and ask whether to stash before continuing.

### 5. Run the experiment

Run `eval_command` from `autoresearch_config.json`. Capture stdout+stderr.

Parse the last line matching `METRIC: <name>=<value>`.

If the command fails or no metric line is found:
- Revert the change: `git checkout -- .`
- Log the failure
- Continue to the next hypothesis

### 6. Compare with best

Use `metric_direction` to determine if the result is an improvement.

**If improved:**
```bash
git add -A
git commit -m "experiment: <hypothesis> → <metric_name>=<new_value> (was <best_value>)"
```
Update `best_value` and `best_commit` in `autoresearch_config.json`.

**If same or worse:**
```bash
git checkout -- .
```
Do NOT commit. The repo stays at the last known-good state.

### 7. Update experiment log

Append to `experiment_log.md`:

```markdown
## Iteration N — YYYY-MM-DD HH:MM
- **Hypothesis**: <what was tried>
- **Code change**: <one-line description of what changed>
- **Result**: <metric_name>=<value>  |  Best so far: <best_value>
- **Outcome**: ✅ Improvement (+X.XX%) / ❌ Regression / ⚠️ Error: <message>
```

Mark the hypothesis as done in `research_directions.md`: change `- [ ]` to `- [x]`.

### 8. Increment counter

Increment `iterations_run` in `autoresearch_config.json`.

### 9. Report and continue

Send a short update to the user:
- What was tried
- Whether it improved things (and by how much)
- Current best metric vs. original baseline

Then: if running via `/loop`, call ScheduleWakeup with `delaySeconds: 60` to schedule the next iteration, passing the original prompt as the loop prompt. Otherwise ask the user: "Continue to next experiment?"

---

## Metric output format

The training script must emit exactly one line:
```
METRIC: <name>=<value>
```

For existing scripts that don't do this, offer to add a single print statement:
```python
# at the end of training
print(f"METRIC: val_loss={val_loss:.4f}")
```

If a script emits multiple metrics, ask the user which one is primary and configure `metric_name` accordingly.

---

## Hypothesis generation tips

Generate hypotheses that are:
- **Atomic**: one change per hypothesis
- **Ordered by expected impact**: start with learning rate and optimizer (high impact) before architecture changes
- **Informed by history**: if Adam outperformed SGD, generate hypotheses about Adam hyperparams next
- **Diverse**: if 3+ consecutive experiments fail, shift to a different category

Avoid:
- Changing multiple hyperparameters at once
- Hypotheses that break the script interface (e.g., changing output format)

---

## Safety rules

- Never `git push` — only local commits
- Never `git reset --hard` or `git push --force`
- Always verify git status before committing
- If the working tree is unexpectedly dirty at loop start, pause and ask the user
- Never delete files unless the user explicitly asks
- Limit total iterations to `max_iterations` (default: 20) — always keep a hard ceiling
