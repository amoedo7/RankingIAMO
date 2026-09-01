#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

repo = os.environ.get("GITHUB_REPOSITORY", "")
current_tag = os.environ.get("CURRENT_TAG", "")
previous_tag = os.environ.get("PREVIOUS_TAG", "")


def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()

if not repo:
    raise SystemExit("GITHUB_REPOSITORY is required")

if not current_tag:
    current_tag = "HEAD"

if previous_tag in ("", "refs/heads/main", "HEAD"):
    tag_list = run(["git", "tag", "--list"]).strip()
    if tag_list:
        previous_tag = run(["git", "describe", "--tags", "--abbrev=0", "HEAD~1"]) if run(["git", "rev-list", "--count", "HEAD"]) != "1" else "HEAD~1"
    else:
        previous_tag = "$(git rev-list --max-parents=0 HEAD)"

log = run(["git", "log", f"{previous_tag}..{current_tag}", "--pretty=format:%h%x09%s"])
items = []
for line in log.splitlines():
    if not line.strip():
        continue
    sha, message = line.split("\t", 1)
    items.append(f"- {message} ({sha[:7]})")

if not items:
    items = ["- No merged work found since the previous tag."]

summary = "\n".join(items)
release_path = Path(".github/release-notes.md")
release_path.parent.mkdir(parents=True, exist_ok=True)
release_path.write_text(f"## Release {current_tag}\n\n{summary}\n", encoding="utf-8")
print(release_path.read_text())