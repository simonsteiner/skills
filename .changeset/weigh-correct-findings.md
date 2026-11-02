---
"simonsteiner-skills": minor
---

address-review-findings and review-prs now weigh a correct finding before fixing it: how likely a real user is to reach the trigger, how bad the outcome is, and whether the fix closes a defect or adds a feature. A finding that's real but not worth fixing in this PR gets a new *deferred* verdict: a reply with the reason, its bot thread resolved, and a line in the report's follow-ups. Fixing every bot finding never converged, because each round lands on the last fix.
