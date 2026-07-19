# Security Policy

## Reporting a Vulnerability

The Vayu-Drishti team takes security seriously. If you discover a security
vulnerability, please **do not** open a public issue.

Instead, send a private report to the repository maintainers.

### What to include

- A brief description of the vulnerability
- Steps to reproduce it
- Potential impact
- Any suggested remediation (optional)

### What to expect

- Acknowledgment within 48 hours
- A timeline for investigation and fix
- Credit in release notes once resolved

## Secure Development Guidelines

1. **Never commit secrets.** API keys, tokens, passwords, and certificates
   must use environment variables (`.env`) or a secrets manager.

2. **Validate all inputs.** All API endpoints validate input via Pydantic
   models. Never disable validation.

3. **Dependency scanning.** Run `pip-audit` and `npm audit` regularly.

4. **Least privilege.** Services run as non-root. Database users have
   minimal required permissions.

5. **HTTPS in production.** Never expose the API over plain HTTP in a
   production environment.

## Configuration Security

- The `.env` file is in `.gitignore` and must never be committed.
- Use `.env.example` as a template — fill in real values only in `.env`.
- Rotate secrets before moving from development to production.
