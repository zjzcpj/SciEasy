#!/bin/bash
# Claude Code PreToolUse hook: check workflow gate before git push
# Ensures agents complete docs + changelog gates before pushing.

set -e

INPUT=$(cat)
CMD=$(echo "$INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Only intercept git push commands
if ! echo "$CMD" | grep -qE '^git push'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Extract branch name from push command or current branch
BRANCH=$(git branch --show-current 2>/dev/null || echo "")

# Only enforce for branches that require gates (feat/, fix/, refactor/)
if [ -z "$BRANCH" ] || ! echo "$BRANCH" | grep -qE '^(feat|fix|refactor)/'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Check if there's an active workflow for this branch
GATE_OUTPUT=$(python .workflow/gate.py list 2>/dev/null || echo "")

# If no gate.py or no workflows, allow (not all branches use gates)
if [ -z "$GATE_OUTPUT" ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Find active workflow matching this branch (heuristic: check if any active workflow exists)
ACTIVE=$(echo "$GATE_OUTPUT" | grep "active" | head -1)
if [ -z "$ACTIVE" ]; then
  # No active workflow — either completed or not using gates
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Extract task ID from the active workflow line
TASK_ID=$(echo "$ACTIVE" | awk '{print $1}')

# Check gate status
STATUS=$(python .workflow/gate.py status "$TASK_ID" 2>/dev/null || echo "")

# Check that create_branch is at least DONE (minimum for pushing)
if echo "$STATUS" | grep -q "Create Branch.*DONE"; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

# Block: gate not ready for push
echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"WORKFLOW GATE: create_branch stage not completed. Run: python .workflow/gate.py status $TASK_ID\"}}"
exit 0