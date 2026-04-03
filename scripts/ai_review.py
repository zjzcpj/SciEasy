#!/usr/bin/env python3
"""AI-powered PR review using Codex agent.

Triggered by GitHub Actions on new/updated PRs. Fetches the PR diff,
sends it to a Codex agent with the review prompt, and posts the
review as a PR comment.

Environment variables (set by GitHub Actions):
    GITHUB_TOKEN   - GitHub token for API access
    OPENAI_API_KEY - OpenAI API key for Codex agent
    PR_NUMBER      - Pull request number
    REPO_NAME      - Repository in owner/repo format
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REVIEW_PROMPT_PATH = Path(__file__).parent / "prompts" / "review_agent_prompt.md"

# Truncate large diffs to stay within model context limits
MAX_DIFF_CHARS = 80_000


def get_pr_diff(repo: str, pr_number: int) -> str:
    """Fetch PR diff via gh CLI."""
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/pulls/{pr_number}",
            "-H", "Accept: application/vnd.github.diff",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def get_pr_metadata(repo: str, pr_number: int) -> dict:
    """Fetch PR title, body, and changed files via gh CLI."""
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr_number}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def load_review_prompt() -> str:
    """Load the review agent prompt template."""
    if not REVIEW_PROMPT_PATH.exists():
        print(f"Warning: {REVIEW_PROMPT_PATH} not found, using default prompt")
        return (
            "Review this pull request for correctness, style, and potential issues. "
            "Be concise and actionable."
        )
    return REVIEW_PROMPT_PATH.read_text(encoding="utf-8")


def run_codex_review(prompt: str, diff: str, metadata: dict) -> str:
    """Invoke the Codex CLI agent in headless mode and return its output."""
    title = metadata.get("title", "Untitled")
    body = metadata.get("body") or "No description provided."
    number = metadata.get("number", "?")

    # Truncate diff if needed
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n... [diff truncated] ..."

    full_prompt = (
        f"{prompt}\n\n"
        f"---\n\n"
        f"# PR #{number}: {title}\n\n"
        f"## Description\n{body}\n\n"
        f"## Diff\n```diff\n{diff}\n```\n"
    )

    result = subprocess.run(
        [
            "codex",
            "--approval-mode", "full-auto",
            "--quiet",
            full_prompt,
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        stderr_snippet = result.stderr[:500] if result.stderr else "(no stderr)"
        print(f"Codex agent failed (rc={result.returncode}): {stderr_snippet}", file=sys.stderr)
        return (
            "**Codex review agent encountered an error.**\n\n"
            f"```\n{stderr_snippet}\n```"
        )

    return result.stdout.strip()


def post_review_comment(repo: str, pr_number: int, body: str) -> None:
    """Post the review as a PR issue comment via gh CLI."""
    subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/issues/{pr_number}/comments",
            "-f", f"body={body}",
        ],
        check=True,
    )


def main() -> None:
    repo = os.environ.get("REPO_NAME")
    pr_number_str = os.environ.get("PR_NUMBER")

    if not repo or not pr_number_str:
        print("Error: REPO_NAME and PR_NUMBER environment variables required", file=sys.stderr)
        sys.exit(1)

    pr_number = int(pr_number_str)
    print(f"Reviewing PR #{pr_number} in {repo} ...")

    # 1. Fetch PR data
    metadata = get_pr_metadata(repo, pr_number)
    diff = get_pr_diff(repo, pr_number)

    if not diff.strip():
        print("Empty diff — skipping review.")
        return

    # 2. Load review prompt
    prompt = load_review_prompt()

    # 3. Run Codex agent
    review = run_codex_review(prompt, diff, metadata)

    # 4. Post review comment
    comment = (
        "## Codex AI Review\n\n"
        f"{review}\n\n"
        "---\n"
        "*Automated review by Codex agent*"
    )
    post_review_comment(repo, pr_number, comment)
    print(f"Review posted on PR #{pr_number}.")


if __name__ == "__main__":
    main()
