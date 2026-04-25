# adversarial-research

Adversarial extension of the [`autoresearch`](../autoresearch/SKILL.md) skill. Adds two adversarial dynamics on top of the base experiment loop. They can be used independently or combined.

| Mode | What it adds | When to use |
|------|--------------|-------------|
| **A — `adversarial-gvc`** | A Critic agent vets every hypothesis **before** it runs | Noisy hypothesis spaces; want a quality gate; tired of running redundant experiments |
| **B — `adversarial-task`** | Two competing metrics inside one experiment + collapse watcher | GAN-style training; fairness vs accuracy; multi-objective work |
| **A+B — `adversarial-gvc+task`** | Both — critic over a two-metric task | Full adversarial-research setup |

## How to activate

Open a project containing this skill in Claude Code. Trigger phrases:

- `запусти adversarial research` / `start adversarial research` → asks which mode
- `запусти generator vs critic` / `start gvc` → mode A
- `запусти adversarial training` / `start adversarial task` → mode B
- `запусти adversarial loop` / `start adversarial loop` → mode A+B (combined)

If a project already has a base `autoresearch_config.json`, the skill will offer to upgrade it without losing `best_value` or `iterations_run` (see [Upgrade Path](SKILL.md#upgrade-path) in the SKILL).

## Files in this skill

```
adversarial-research/
├── SKILL.md                              # main skill instructions
├── prompts/
│   ├── generator.md                      # Generator role (mode A, A+B)
│   ├── critic.md                         # Critic role (mode A, A+B)
│   └── balance_watcher.md                # Collapse watcher (mode B, A+B)
├── templates/
│   ├── research_directions_gvc.md        # mode A initial hypotheses
│   ├── research_directions_task.md       # mode B/A+B initial hypotheses (with [primary]/[adversary]/[both] tags)
│   └── experiment_log_entry.md           # log formats per mode
└── README.md                             # you are here
```

Edit `prompts/*.md` to tune role behavior without touching `SKILL.md`.

---

## Example: full cycle in mode A (`adversarial-gvc`)

User runs `start gvc` in a fresh repo. Onboarding fills `autoresearch_config.json`:

```json
{
  "mode": "adversarial-gvc",
  "metric_name": "val_loss",
  "metric_direction": "lower_is_better",
  "best_value": 0.4231,
  "iterations_run": 0,
  "max_iterations": 20,
  "critic_max_revisions": 2,
  "eval_command": "python train.py --epochs 5 --seed 42"
}
```

### Iteration 5 walkthrough

**Generator output:**
```
HYPOTHESIS: Lower learning rate from 1e-3 to 5e-4 — recent SGD experiments hit a noise floor; smaller LR may give cleaner descent.
EXPECTED: val_loss to drop modestly (1–4%). No risk of training instability at this scale.
PATCH:
- optimizer = optim.Adam(model.parameters(), lr=1e-3)
+ optimizer = optim.Adam(model.parameters(), lr=5e-4)
```

**Critic output:**
```
1. Novelty: lr=5e-4 has not been tried (iter 2 used 1e-2, iter 3 used 1e-3 baseline, iter 4 used SGD).
2. Realism: 1–4% drop is plausible for a halved Adam lr at this scale.
3. Risks: none — slower learning at worst.
4. Patch: clean, single-line, output format intact.

VERDICT: APPROVE
```

**Run:** `python train.py --epochs 5 --seed 42` → `METRIC: val_loss=0.4087`.

**Decision:** 0.4087 < 0.4231 → improvement. `git commit -m "experiment: lr=5e-4 → val_loss=0.4087 (was 0.4231) [critic: APPROVE]"`. `best_value` updated.

**Log entry appended:**
```markdown
## Iteration 5 — 2026-04-25 09:42
- **Hypothesis**: Lower learning rate from 1e-3 to 5e-4
- **Critic verdict**: APPROVE
- **Code change**: lr 1e-3 → 5e-4 in Adam
- **Result**: val_loss=0.4087  |  Best so far: 0.4087
- **Outcome**: ✅ Improvement (-3.40%)
```

### When the critic rejects

Iteration 11, Generator suggests trying lr=5e-4 again. Critic catches it:

```
1. Novelty: this exact value was tried in iteration 5 (val_loss=0.4087). Duplicate.
VERDICT: REJECT — duplicate of iteration 5
```

Logged as `🚫 Rejected before execution`. No run. Move on.

---

## Example: full cycle in mode B (`adversarial-task`)

GAN training. `train.py` outputs two metrics last:

```
METRIC: fid=42.31
METRIC: balance=0.18
```

`balance` here = abs(D_real_acc - 0.5) — discriminator drifting from indecision is bad. `fid` is the primary objective (lower better), `balance` is the constraint (also lower better, threshold 1.5× of best).

Config:
```json
{
  "mode": "adversarial-task",
  "metrics": [
    {"name": "fid", "direction": "lower_is_better", "role": "primary"},
    {"name": "balance", "direction": "lower_is_better", "role": "adversary"}
  ],
  "metric_name": "fid",
  "metric_direction": "lower_is_better",
  "best_value": 45.10,
  "best_adversary": 0.20,
  "scoring_formula": "commit_if_primary_improved_and_adversary_within_threshold",
  "adversary_threshold": 1.5,
  "collapse_window": 3,
  "iterations_run": 0,
  "max_iterations": 30
}
```

### Iteration 7 walkthrough

Hypothesis from `research_directions.md`: `[primary] Try generator lr 5e-5`.

Run: `METRIC: fid=42.31`, `METRIC: balance=0.18`.

Decision via formula:
- fid: 42.31 < 45.10 → primary improved ✅
- balance threshold: 1.5 × 0.20 = 0.30. 0.18 ≤ 0.30 → within threshold ✅
- Both conditions hold → commit.

`best_value` ← 42.31, `best_adversary` ← 0.18.

```markdown
## Iteration 7 — 2026-04-25 14:15
- **Hypothesis**: [primary] Try generator lr 5e-5
- **Code change**: G optimizer lr 1e-4 → 5e-5
- **Result**: fid=42.31 (was 45.10) | balance=0.18 (was 0.20)
- **Outcome**: ✅ Both improved
```

### Watcher fires

By iteration 12, the last 3 runs improved `fid` but pushed `balance` from 0.18 → 0.21 → 0.24 → 0.28 (degrading every iteration; new threshold = 1.5 × 0.18 = 0.27 → just exceeded). Watcher invoked:

Watcher output prepended to `research_directions.md`:
```markdown
- [ ] [adversary] [priority] Add label smoothing 0.1 to discriminator real labels
- [ ] [both] [priority] Lower D update frequency: train D every 2 G steps
```

These run next. Loop continues normally — they go through scoring just like any other hypothesis.

---

## Example: full cycle in mode A+B (`adversarial-gvc+task`)

Combine the two. The Critic now also checks whether the Generator's `TARGET` tag matches the patch.

Config: same as mode B but with `"mode": "adversarial-gvc+task"` and `"critic_max_revisions": 2`.

### Iteration 14 walkthrough

**Generator:**
```
HYPOTHESIS: Add label smoothing 0.1 to D real labels to relax discriminator confidence.
TARGET: [adversary]
EXPECTED: balance metric drops 10–20% (D becomes less certain), fid roughly stable or slight regression.
PATCH:
+ real_labels = torch.full_like(real_labels, 0.9)  # was 1.0
```

**Critic:**
```
1. Novelty: not tried; the watcher proposed this 2 iterations ago.
2. Realism: label smoothing on the strong side typically does reduce D confidence; effect size plausible.
3. Risks: fid could regress if D becomes too weak; threshold guard handles this.
4. Patch: matches TARGET tag ([adversary]). Output format intact (still emits both METRIC: lines).

VERDICT: APPROVE
```

Run: `fid=43.02` (was 42.31, slight regression), `balance=0.19` (was 0.28, big improvement).

Decision: primary regressed → revert. Log:

```markdown
## Iteration 14 — 2026-04-25 16:08
- **Hypothesis**: [adversary] Add label smoothing 0.1 to D real labels
- **Critic verdict**: APPROVE
- **Code change**: D real labels 1.0 → 0.9 (smoothing)
- **Result**: fid=43.02 (was 42.31) | balance=0.19 (was 0.28)
- **Outcome**: ❌ Primary regression
```

Critic gets a "missed something" note for the next iteration's prompt context. Loop continues.

---

## Bilingual triggers

Both modes onboard and respond in the user's language. First user message determines the language; that choice is preserved for the session. Trigger phrases work in either language.

## What this skill never does

- Pushes to a remote (no `git push`)
- Force-resets the working tree (no `git reset --hard`)
- Deletes files
- Bypasses `max_iterations`
- Runs experiments without a clean working tree

These are inherited from the base skill and tightened in `SKILL.md` under "Safety rules".
