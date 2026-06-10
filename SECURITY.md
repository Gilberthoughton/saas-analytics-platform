# Security Policy

## Supported versions

This is a portfolio project; the latest `main` is the only supported version.

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Instead report
privately via one of:

- GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  (**Security → Report a vulnerability**), or
- email **houghtongilbert@gmail.com**.

Please include reproduction steps and impact. I aim to acknowledge reports
within a few days.

## Security design notes

- Passwords are stored as bcrypt hashes; API keys are stored as SHA-256 hashes
  with only a non-secret prefix retained for display.
- Authentication uses signed JWTs (dashboard) and `X-API-Key` (ingestion).
- Multi-tenant isolation is enforced at the repository layer — every query is
  scoped by `organization_id`.
- Example secrets in `.env.example` / `docker-compose.yml` are for local use
  only and must be replaced before any deployment.
- Dependency updates are tracked via Dependabot.
