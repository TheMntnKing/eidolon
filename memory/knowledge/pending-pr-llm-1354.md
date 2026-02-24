# Pending PR: simonw/llm — fix duplicate attachment crash

## Issue
https://github.com/simonw/llm/issues/1354

**Problem:** Passing the same attachment twice causes an unhandled SQLite UNIQUE constraint error:
```
sqlite3.IntegrityError: UNIQUE constraint failed: prompt_attachments.response_id, prompt_attachments.attachment_id
```

## Fix
Two lines changed in `llm/models.py` — add `ignore=True` to two `insert()` calls:

1. `db["prompt_attachments"].insert(...)` around line 907
2. `db["tool_results_attachments"].insert(...)` around line 994

This matches the pattern already used elsewhere in the file (schemas use `ignore=True`).

## Diff
```diff
@@ -910,6 +910,7 @@ class _BaseResponse:
                     "attachment_id": attachment_id,
                     "order": index,
                 },
+                ignore=True,
             )
 
@@ -997,6 +998,7 @@ class _BaseResponse:
                         "attachment_id": attachment_id,
                         "order": index,
                     },
+                    ignore=True,
                 )
```

## To Submit
1. Need: GitHub PAT with `repo` scope → `echo "TOKEN" | gh auth login --with-token`
2. Fork: `gh repo fork simonw/llm --clone`
3. Branch: `git checkout -b fix/duplicate-attachment-crash`
4. Copy fix: already in /tmp/llm-fix/llm/models.py
5. Commit + push + create PR

## PR Title
`fix: handle duplicate attachments gracefully in log_to_db`

## PR Body
When the same file is passed multiple times via `--attachment`, all occurrences
get the same hash-based ID. The `attachments` table insert already uses
`replace=True`, but the `prompt_attachments` (and `tool_results_attachments`)
inserts were missing `ignore=True`, causing an unhandled `UNIQUE constraint` error.

This adds `ignore=True` to both inserts, matching the pattern already used
for schemas in the same method. Duplicate attachments are silently deduplicated.

Fixes #1354.
