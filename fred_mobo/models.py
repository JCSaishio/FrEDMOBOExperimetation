"""Section B — Gaussian process surrogates.

Algorithm 2. One independent GP per modeled outcome via ``ModelListGP``: three outcomes
in mode A (diameter, power, margin), two in mode B.

The kernel is set *explicitly* — ``ScaleKernel(MaternKernel(nu=2.5, ard))`` by default,
``ScaleKernel(RBFKernel(ard))`` as the operator-selectable alternative — rather than
relying on BoTorch's current ``SingleTaskGP`` default, so that what the paper states is
what actually ran. Matern-5/2 is the default because it assumes only twice-
differentiable sample paths, a weaker and more defensible smoothness claim near a
failure boundary than the infinitely-smooth SE.

Noise is inferred by ML-II. The within-run standard error of equation (3) captures
measurement scatter only, while the dominant noise on this device is run-to-run;
``train_Yvar = SE^2`` stays available as a switchable sensitivity check.

Models are re-initialized and refit from scratch after every new run — no warm start of
hyperparameters (§9.2 item 2).

Implements: §3, Algorithm 2, equations (4)-(9)
Public interface (§7.1): ``fit_models(data, cfg) -> (ModelListGP, FitReport)``
"""
