# Release Ship Pack

This bundle gives a small team a reusable GitHub Actions workflow to automate release notes, labels and deploy summaries.

## Included
- `.github/workflows/release-ship-pack.yml`
- `.github/scripts/release_summary.py`
- `templates/changelog.md`
- `docs/setup.md`

## Quick start
1. Copy the workflow into your repo.
2. Add `GH_TOKEN`, `SLACK_WEBHOOK_URL`, and optionally `EMAIL_TO` as repository secrets.
3. Push to `main` or create a tag.

## What it does
- Collects merged PRs between tags.
- Builds a changelog from conventional commits.
- Applies labels to tickets and releases.
- Sends a deploy summary to Slack or email.

## Payment
Reference: RANK-IAMO519

## License
MIT