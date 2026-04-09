PR_BODY="macOS GUI application commands (like Fiji or \`open\`) often behave as
launchers, spawning a background process and immediately exiting
with code 0. Previously, FileWatcher would see the process exit and
immediately raise ProcessExitedWithoutOutputError, causing the
workflow to fail silently.

This change adds \`exit_info()\` to \`_PopenProcessAdapter\` to expose
the exit code, and updates \`FileWatcher\` so that if the process exits
successfully with 0, it assumes background execution and continues
polling for files until timeout.

Closes #420

---
*PR created automatically by Jules for task [1034323228105571478](https://jules.google.com/task/1034323228105571478) started by @zjzcpj*
"
echo "$PR_BODY" | grep -qiE "(closes|fixes|resolves)\s+#[0-9]+" && echo "PASSED" || echo "FAILED"
