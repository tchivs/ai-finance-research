# Source Sync Schema

`source-sync.json` is the machine-readable handoff between the Git updater and the documentation agent.

## Project record

```json
{
  "source_dir": "qlib",
  "remote": "https://github.com/microsoft/qlib.git",
  "status": "updated",
  "before": {
    "head": "<OLD_COMMIT>",
    "head_short": "<OLD_SHORT>",
    "branch": "main",
    "upstream": "origin/main",
    "dirty": false
  },
  "after": {
    "head": "<NEW_COMMIT>",
    "head_short": "<NEW_SHORT>",
    "branch": "main",
    "upstream": "origin/main",
    "dirty": false
  },
  "changed_files": [
    "M\tpath/to/module.py",
    "A\tpath/to/new_module.py"
  ],
  "commits_added": 2,
  "doc_dir": "qlib",
  "doc_action": "metadata_updated"
}
```

## Status values

- `updated`: fast-forwarded to a new commit; inspect `changed_files`.
- `unchanged`: pull completed and HEAD did not move.
- `not_pulled`: inspection only; no network update was requested.
- `dry_run`: preview mode.
- `skipped_dirty`: local changes were detected; preserve them and review manually.
- `skipped_detached`: repository is not on a branch.
- `skipped_no_upstream`: current branch has no configured upstream.
- `fetch_failed` / `pull_failed`: source update needs manual resolution.
