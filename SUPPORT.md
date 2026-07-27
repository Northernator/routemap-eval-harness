# Support

RouteMap is maintained as an open-source research project on a best-effort basis. No response time, production
support, or compatibility guarantee is provided.

## Where to ask

- **Bug:** open a bug report with a minimal synthetic reproduction.
- **Feature or design proposal:** open a feature request and explain the reliability use case and affected lane.
- **Usage question:** search existing issues, then open an issue if the answer is not in
  [`README.md`](README.md) or [`docs/RUNNING.md`](docs/RUNNING.md).
- **Security vulnerability:** follow [`SECURITY.md`](SECURITY.md); do not disclose details in an issue.
- **Sensitive conduct report:** follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- **Provider, Ollama, GPU, or driver problem:** first verify it against the provider or hardware project's
  documentation; RouteMap maintainers can address only repository-owned behavior.

## Information to include

- RouteMap full commit hash (`git rev-parse HEAD`);
- Python version and operating system;
- installation command and relevant dependency versions;
- exact command or UI action;
- expected and actual result;
- complete error text with credentials, tokens, usernames, local paths, and private prompts redacted; and
- smallest synthetic input that reproduces the problem.

Generated `EVIDENCE/` and audit/run files can contain prompts or model output. Review and redact them before
sharing. Never post API keys, bearer tokens, `.env` contents, customer data, or proprietary model inputs.
