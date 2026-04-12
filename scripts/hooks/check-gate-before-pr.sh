#!/bin/bash
# Claude Code PreToolUse hook: check workflow gate before gh pr create
# Ensures agents complete update_docs + update_changelog before creating PR.

set -e

INPUT=$(cat)
CMD=$(echo "$INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Only intercept gh pr create commands
if ! echo "$CMD" | grep -qE 'gh pr create'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Only enforce for branches that require gates (feat/, fix/, refactor/)
BRANCH=$(git branch --show-current 2>/dev/null || echo "")
if ! echo "$BRANCH" | grep -qE '^(feat|fix|refactor)/'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Check if there's an active workflow
GATE_OUTPUT=$(python .workflow/gate.py list 2>/dev/null || echo "")

if [ -z "$GATE_OUTPUT" ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

ACTIVE=$(echo "$GATE_OUTPUT" | grep "active" | head -1)
if [ -z "$ACTIVE" ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

TASK_ID=$(echo "$ACTIVE" | awk '{print $1}')
STATUS=$(python .workflow/gate.py status "$TASK_ID" 2>/dev/null || echo "")

# Check that update_changelog is DONE (gate 5 of 6, right before submit_pr)
if echo "$STATUS" | grep -q "\[DONE\].*Update Changelog"; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Check which gates are missing
MISSING=""
echo "$STATUS" | grep -q "\[DONE\].*Update Documentation" || MISSING="update_docs "
echo "$STATUS" | grep -q "\[DONE\].*Update Changelog" || MISSING="${MISSING}update_changelog"

echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"WORKFLOW GATE: Missing stages before PR: ${MISSING}. Run: python .workflow/gate.py status $TASK_ID\"}}"
exit 0
