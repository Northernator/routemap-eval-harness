# RouteMap Evaluation Harness Agent Notes

## Project goal

Make this harness a runnable local evaluation project for comparing RouteMap retrieval against simple keyword retrieval, optional neural embedding retrieval, and optional LLM route extraction.

## Coding conventions

- Keep the default demo fully local and deterministic; it must not require external APIs.
- Keep optional integrations isolated in their own scripts and document extra dependencies separately.
- Prefer small CSV fixtures under `data/gold/` for sample evaluation inputs.
- Write generated demo outputs under `data/outputs/`.
- Preserve the script-per-task layout in `src/`; avoid broad framework rewrites.
- Use standard-library Python where practical. Keep required dependencies minimal and explicit.
- When adding CLI behavior, keep arguments explicit and compatible with existing scripts.
- Favor readable metrics CSVs over hidden state or notebook-only workflows.
