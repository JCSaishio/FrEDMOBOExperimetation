"""Section E.2 — export for downstream agents.

Three files together. ``campaign_export.json`` is the machine-readable source of truth;
``campaign_summary.md`` is the same content as prose and tables, because LLMs reason
better over prose-plus-tables than over raw JSON; ``pareto_points.csv`` is a flat table
for spreadsheets.

The ``maps`` block is mandatory: posterior mean and sd of each outcome, Pr(F) and the
R-band on a grid over the design space. The downstream agent computes with the *maps*,
not the fronts — for any requested ``d*`` it derives the iso-diameter curve itself, and
corrects using the map's local slope, bounded by the R-band and the diameter band so it
can never step into a failure region (§5.5).

Every exported point carries its uncertainty, so an agent picking a set-point is told
how sure the model is.

Implements: §6.2, §5.5
Public interface (§7.1): ``export_campaign(campaign, out_dir)``
"""
