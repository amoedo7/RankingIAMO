# Release Ship Pack setup

1. Create repository secrets: `GH_TOKEN`, `SLACK_WEBHOOK_URL`, and `EMAIL_TO` (optional).
2. Add the workflow file to `.github/workflows`.
3. Add the script to `.github/scripts`.
4. Tag a release with `v1.0.0` to generate the changelog and summary.

## Notes
- The workflow reads merged PR titles since the previous tag.
- Keep commit messages in a conventional format such as `feat:`, `fix:`, or `docs:`.
- For email notifications, connect a mailer action or a transactional email service in your project.