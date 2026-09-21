"""Section D — qLogNEHVI construction and optimization.

Builds the MC objective transform and the acquisition function, then maximizes it.

Objective 1 is ``|d - d*|`` computed *inside* a ``GenericMCMultiOutputObjective`` on
posterior samples of ``d``, never by fitting a GP to ``|d - d*|`` directly: the absolute
value has a crease at ``d*`` that a stationary kernel cannot represent, and a GP fitted
through it fakes the crease with a short length-scale. The same ``d`` GP also carries
the diameter-band feasibility constraint (§2.2, §9.2 item 3).

qLogNEHVI rather than qNEHVI because plain HVI underflows to zero far from the front and
its gradient vanishes; the log reformulation replaces the clamped differences with a
softplus and the sample average with a log-sum-exp. This is an optimization device, not
a better estimator — ``exp`` of (14) equals (13) only in the limit. The paper should say
so (§5.2).

Implements: §5.2, equations (13)-(14), §8 (BoTorch mapping)
Public interface (§7.1): ``propose(model, data, cfg) -> Proposal``
"""
