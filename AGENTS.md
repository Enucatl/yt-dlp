# Agent Instructions

## Formatting

- Do not run `ruff format` in this repository. Upstream yt-dlp is not Ruff-format compliant, and formatting it creates a large unrelated diff.
- Preserve upstream formatting and limit changes to files required by the task.
- `ruff check` may still be used for focused lint verification.
