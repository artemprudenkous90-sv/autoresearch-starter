# Research Directions

Mode A — Generator vs Critic. Hypotheses in this list are seed ideas. The Generator may create new ones at runtime; the Critic may reject any of them. Rejected hypotheses are marked `- [x] (rejected by critic)` so the Generator learns the boundary.

## Active hypotheses
- [ ] Try learning rates: 1e-2, 5e-3, 1e-3, 5e-4, 1e-4
- [ ] Compare optimizers: Adam vs AdamW vs SGD with momentum
- [ ] Add dropout regularization: 0.1, 0.2, 0.3, 0.5
- [ ] Vary batch size: 32, 128, 256, 512
- [ ] Add batch normalization after hidden layers
- [ ] Try weight decay: 1e-4, 1e-3, 1e-2
- [ ] Add learning rate scheduler: CosineAnnealingLR, StepLR
- [ ] Increase model width: hidden=512, 1024
- [ ] Try activation functions: GELU, LeakyReLU instead of ReLU

## Completed
(none yet)

## Rejected by critic
(none yet — Critic rejections appear here automatically)
