"""Section E — the campaign database.

One SQLite file per campaign, with tables ``campaign``, ``runs``, ``sessions`` and
``fits``. A campaign takes several days, so this file is the single source of truth and
the app must close and reopen at any point without loss.

Nothing is pickled. Reopening restores config, every run, every fit report, the
reference-point / bounds / kernel history, the current proposal and the convergence
state; models are then refit *deterministically* from the stored data and seed. Raw
CSVs are copied into the campaign folder so it is self-contained and portable between
machines. Autosave after every intake and every fit (§6.1, §9.2 item 9).

Implements: §6.1
Public interface (§7.1): ``Campaign``, ``add_run``, ``add_fit``, ``export``
"""
