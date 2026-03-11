# Security

## Responsible disclosure

If you discover a security vulnerability in Data Forge, please report it responsibly:

1. **Do not** open a public issue for security-sensitive bugs.
2. Email the maintainers (see repository contacts) or open a **private** security advisory on GitHub if the repo supports it.
3. Include a clear description, steps to reproduce, and impact if possible.
4. Allow a reasonable time for a fix before any public disclosure.

We will acknowledge your report and work on a fix. We appreciate the community’s help in keeping Data Forge safe.

## Data and credentials

- Data Forge runs locally by default; generated data and scenario configs stay on your machine unless you explicitly use cloud adapters (e.g. Snowflake, BigQuery).
- Connection credentials (e.g. `db_uri`, passwords) are masked in saved scenarios; never commit real credentials to the repo or configs.
- Use environment variables or secret managers for production credentials; avoid hardcoding.
