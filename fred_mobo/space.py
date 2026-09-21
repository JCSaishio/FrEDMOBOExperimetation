"""Variable definitions and coordinate maps.

Maps raw engineering set-points to and from the normalized unit cube the GPs and the acquisition
live in, and computes the draw ratio ``R = v_s / v_f`` from set-points.

In 2D, ``v_f`` is fixed, so ``R`` is a known exact function of the spooler set-point; the unknown
is only where the failure boundaries sit in ``R`` and how they move with ``T`` (§4.1). For 3D this
switches to the rotated coordinates ``(log R, log v_f, T)``, whose rectangular raw bounds become a
parallelogram expressed as linear inequality constraints passed to ``optimize_acqf`` (§7.4).

STATUS: the coordinate map is complete. The draw ratio and the 3D rotated coordinates are NOT
implemented — they are blocked on open item A3 (effective spool diameter under load). See
``draw_ratio`` below and docs/PROGRESS.md.

Implements: §1.1, §2.3 step 10 (draw ratio), §7.4 (rotated coordinates)
Public interface (§7.1): ``to_unit``, ``from_unit``, ``bounds``, ``linear_constraints``
"""

from __future__ import annotations

import torch
from botorch.utils.transforms import normalize, unnormalize
from torch import Tensor

from fred_mobo.config import CampaignConfig

__all__ = ["bounds", "to_unit", "from_unit", "unit_bounds", "draw_ratio", "linear_constraints"]

# §9.2 item 1: double precision throughout. float32 causes Cholesky failures on this problem size.
DTYPE = torch.double


def bounds(config: CampaignConfig, *, dtype: torch.dtype = DTYPE) -> Tensor:
    """Raw-space bounds as the ``2 x d`` tensor BoTorch expects.

    Row 0 is lower, row 1 is upper, columns in ``config.variables`` order.
    """
    return torch.tensor(
        [[v.lower for v in config.variables], [v.upper for v in config.variables]],
        dtype=dtype,
    )


def unit_bounds(config: CampaignConfig, *, dtype: torch.dtype = DTYPE) -> Tensor:
    """The unit cube, ``2 x d``. This is what ``optimize_acqf`` is given (§8)."""
    d = config.d
    return torch.stack([torch.zeros(d, dtype=dtype), torch.ones(d, dtype=dtype)])


def to_unit(X_raw: Tensor, config: CampaignConfig) -> Tensor:
    """Map raw set-points onto the unit cube.

    Args:
        X_raw: ``... x d`` tensor of set-points in raw engineering units, columns ordered as
            ``config.variables``.
        config: the campaign configuration supplying the bounds.

    Returns:
        A ``... x d`` tensor in ``[0, 1]^d``.

    Raises:
        ValueError: if ``X_raw``'s trailing dimension does not match ``config.d``.

    Note:
        §8 warns that ``qLogNEHVI`` takes ``X_baseline`` in the *same space the model was trained
        in*; mismatched spaces are a silent bug. Everything downstream of this function is in unit
        space, and display un-negates and un-normalizes at the boundary.
    """
    X_raw = _check(X_raw, config, "X_raw")
    return normalize(X_raw, bounds(config, dtype=X_raw.dtype))


def from_unit(X_unit: Tensor, config: CampaignConfig) -> Tensor:
    """Map unit-cube points back to raw set-points. Inverse of :func:`to_unit`.

    Args:
        X_unit: ``... x d`` tensor in ``[0, 1]^d``.
        config: the campaign configuration supplying the bounds.

    Returns:
        A ``... x d`` tensor in raw engineering units.
    """
    X_unit = _check(X_unit, config, "X_unit")
    return unnormalize(X_unit, bounds(config, dtype=X_unit.dtype))


def _check(X: Tensor, config: CampaignConfig, name: str) -> Tensor:
    if X.ndim == 0:
        raise ValueError(f"{name} must have at least one dimension")
    if X.shape[-1] != config.d:
        raise ValueError(
            f"{name} has trailing dimension {X.shape[-1]}, but the config declares "
            f"{config.d} variable(s): {[v.name for v in config.variables]}"
        )
    return X


def draw_ratio(*args, **kwargs):  # noqa: ANN002, ANN003, ANN201
    """Draw ratio ``R = v_s / v_f`` from set-points (§2.3 step 10).

    NOT IMPLEMENTED — blocked on open item A3.

    The formula itself is not in doubt::

        v_s = pi * D_eff * omega_s      take-up linear speed
        v_f = l_f * omega_f             feed linear speed
        R   = v_s / v_f

    What is in doubt is ``D_eff``. ``DeviceConfig.d_spool_mm`` is the *core* diameter, measured at
    15 mm with a vernier. Using it gives ``R = 93.7`` at the reference run's set-points, hence
    ``d_out = d_in / sqrt(R) = 0.72 mm`` for a 7 mm preform — against an observed plateau near
    0.48 mm, which instead implies an effective diameter around 34 mm. Fibre accumulation is the
    obvious candidate, but it has not been measured.

    Implementing this now would mean choosing between two values that disagree by a factor of 2.3
    and then building the constraint model (§4), the iso-diameter inversion (§5.5) and the 3D
    rotated coordinates (§7.4) on top of that guess. ``R`` is described in §4.1 as "the leading
    quantity for the constraint", so a wrong choice propagates everywhere.

    TODO(resume): implement once A3 lands. Needed: the wound-spool diameter under load, or a
    decision to model accumulation explicitly. Then fill in ``tests/test_space.py::
    test_draw_ratio_against_hand_calculation``, which is the M1 acceptance test.
    """
    raise NotImplementedError(
        "draw_ratio is blocked on open item A3 (effective spool diameter under load). "
        "See docs/PROGRESS.md and FrED_MOBO_Open_Items.docx item A3."
    )


def linear_constraints(*args, **kwargs):  # noqa: ANN002, ANN003, ANN201
    """Linear inequality constraints for the 3D rotated coordinates (§7.4).

    NOT IMPLEMENTED — blocked on open item A3, transitively.

    Going to 3D switches the coordinates to ``(log R, log v_f, T)``, in which the rectangular raw
    bounds become a parallelogram. That parallelogram is expressed to ``optimize_acqf`` through
    ``inequality_constraints``, in the form ``sum_i coef_i * x[idx_i] >= rhs`` (§8).

    This is built on ``R``, so it cannot be written before :func:`draw_ratio`.

    TODO(resume): implement after ``draw_ratio``, together with
    ``tests/test_space.py::test_3d_parallelogram_constraint``.
    """
    raise NotImplementedError(
        "linear_constraints is blocked on open item A3, via draw_ratio. "
        "Phase 2D does not need it: the box is rectangular and plain bounds suffice."
    )
