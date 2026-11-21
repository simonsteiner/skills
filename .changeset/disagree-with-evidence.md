---
"simonsteiner-skills": patch
---

address-review-findings disagrees only with evidence the reviewer can open; "this was intentional" becomes a question for the user instead. A reviewer's misreading still gets a clarity fix, and a finding is fixed as raised or disputed openly, never quietly downgraded. Adapted from Google's Elephant-Goldfish Model. `pick-repo.sh` now places each PR on its repo in a fork checkout, and `--head` exits 1 on a failed `gh` call instead of reading as "no PR".
