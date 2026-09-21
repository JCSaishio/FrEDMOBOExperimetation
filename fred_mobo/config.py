"""Typed campaign configuration.

Holds every numeric the campaign runs on. Per §9.2 item 7 *everything* here is an
operator-editable default with one exception: ``n_0 = 6`` is fixed. The kernel choice
locks after the first adaptive run is accepted.

Dimension-agnostic by construction (§7.4): variables and objectives are *lists*, so
the 2D -> 3D extension is a config change rather than a code path.

Implements: §1.1 (what is optimized), §9.2 item 7, §7.4 (extension to 3D)
Public interface (§7.1): ``CampaignConfig``, ``load``, ``save``
"""
