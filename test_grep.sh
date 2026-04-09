PR_BODY="Closes #420"
echo "$PR_BODY" | grep -qiE '(closes|fixes|resolves)[[:space:]]+#[0-9]+' || echo "FAILED"
