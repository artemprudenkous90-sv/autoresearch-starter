# Research Directions

Mode B (or A+B) — Adversarial Task. Each hypothesis is tagged with which metric it primarily affects: `[primary]`, `[adversary]`, or `[both]`. The `[priority]` tag (added by the Balance Watcher) means "run this next". Order in the file is execution order.

## Active hypotheses

### Primary metric (target of optimization)
- [ ] [primary] Try learning rates on generator: 1e-3, 5e-4, 1e-4
- [ ] [primary] Add weight decay 1e-4 to primary optimizer
- [ ] [primary] Increase generator capacity (hidden=512)
- [ ] [primary] Try AdamW instead of Adam on primary

### Adversary metric (constraint side)
- [ ] [adversary] Add label smoothing 0.1 to discriminator
- [ ] [adversary] Lower discriminator learning rate to 5e-4
- [ ] [adversary] Add dropout 0.2 to discriminator
- [ ] [adversary] Use spectral normalization on discriminator

### Joint changes
- [ ] [both] Try gradient penalty (WGAN-GP style)
- [ ] [both] Adjust update ratio: D updates per G update (1, 2, 5)
- [ ] [both] Add warmup phase: only G for first 200 steps

## Completed
(none yet)

## Rejected by critic
(none yet — only relevant in mode A+B)
