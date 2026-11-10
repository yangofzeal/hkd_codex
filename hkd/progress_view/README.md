# Persistent project progress

One bar per task, with explicit estimate labels and saved evidence timestamps. Runtime snapshots and imported logs remain outside the repository.

## Run on the current Mac

Python 3.9 or later and its standard library are sufficient; no pip dependencies.

```sh
cd ~/Downloads/Project-Progress
python3 build_dashboard.py
python3 web_view.py
```

Open http://127.0.0.1:8769/ in a browser on that Mac. Leave the command running; Ctrl-C stops it. Start Web View.command performs these steps when run with sh. This is a read-only view of the progress table, not an interactive iTerm2 session or a remote terminal stream.

For the terminal table, run `python3 progress_console.py` in another window. It checks imported logs every 30 seconds; the browser reloads its saved page every 30 seconds. Neither process contacts remote workers. Existing display processes must be restarted to load updated Python code.

To use this repository copy with an existing local data directory:

```sh
HKD_PROGRESS_ROOT="$HOME/Downloads/Project-Progress" python3 hkd/progress_view/build_dashboard.py
HKD_PROGRESS_ROOT="$HOME/Downloads/Project-Progress" python3 hkd/progress_view/progress_console.py
python3 hkd/progress_view/web_view.py --root "$HOME/Downloads/Project-Progress"
```

The builder reads sibling `old-mac-codex-logs/*.jsonl` and optional `additional-tasks.json`. It preserves prior output if no complete project snapshot is found. Input fingerprints skip unchanged log parsing. Output replacement is atomic per file; files are not a cross-file transaction. Percentages remain estimates and do not increase merely because time passes.

## Native integration

The local fork patch in `native-widget-path.patch` adds an absolute `CODEX_PROJECT_PROGRESS_PATH` override to its existing declarative widget reader. It needs that reader to exist; it is not a standalone feature for an upstream build. Native compilation and release validation have not been performed. Do not change an installed release or its integrity manifests merely to activate these bars.

## Continuation requirements

Continue runnable authorized work. Respect pauses, cancellations, approval requirements and security boundaries. Persist work state and blockers; do not fabricate activity. Before any restart, confirm the job is absent and eligible, and use duplicate prevention plus bounded retries. Blocked jobs must remain blocked until their prerequisite changes.

The user requested a 0.5-second local continuation check. No such job-restart daemon was verified or installed here. `serve_forever(poll_interval=0.5)` is only the HTTP server shutdown polling interval; it does not resume Codex, restart builds, or prove non-idle behavior. Network health polling must remain at least 30 seconds apart.

## Validation and limitations

Run `python3 -m unittest discover -s hkd/progress_view -p 'test_*.py'`. Route tests cover allowed snapshot paths, rejected arbitrary/traversal paths, and missing files. A listening socket could not be opened inside the agent sandbox; normal-terminal startup and browser appearance remain to be verified. Only loopback access is configured. WAN publication requires a separately authenticated deployment and regional checks.

## Pending questions

Optional `pending-questions.json` in the data directory stores objects with string fields `id`, `text`, `status`, and `dependent_task`. Only `status: pending` is displayed. Questions remain in a sticky panel and in the terminal output until explicitly answered or withdrawn. Reply in Codex; this read-only viewer does not submit answers. Invalid input preserves the prior snapshot. No questions are synthesized by the renderer.

The accompanying task-continuity source mirrors the local fork and records minimal-question and asynchronous-question behavior. This source is not a compiled or activated release, and linking into this GitHub branch must be checked during native integration.
