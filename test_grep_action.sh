PR_BODY="macOS GUI application commands (like Fiji or \`open\`) often behave as
launchers, spawning a background process and immediately exiting
with code 0. Previously, FileWatcher would see the process exit and
immediately raise ProcessExitedWithoutOutputError, causing the
workflow to fail silently.

This change adds \`exit_info()\` to \`_PopenProcessAdapter\` to expose
the exit code, and updates \`FileWatcher\` so that if the process exits
successfully with 0, it assumes background execution and continues
polling for files until timeout.

Closes #420"

if ! echo "$PR_BODY" | grep -qiE "(closes|fixes|resolves)\s+#[0-9]+"; then
  echo "::error::PR must link an issue (e.g. 'Closes #42')"
fi
echo "PASSED"
