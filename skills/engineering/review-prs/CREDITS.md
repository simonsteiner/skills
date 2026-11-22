# Credits

The smell baseline, the Standards and Spec axes, and the "standards files must be on the list" rule in `LENSES.md` are adapted from the MIT-licensed `code-review` skill in <https://github.com/mattpocock/skills>. The smells come from Fowler's *Refactoring*, ch. 3.

The rule that a test expectation changed alongside the code it tests needs a reason from the intended behaviour is an idea from the `ship-pr` and `autopilot` skills in <https://github.com/kentcdodds/kcd-skills>, reworded; no text is carried over.

The Security lens in `LENSES.md` (the boundary-and-result test, the defense-in-depth and source-visibility rules, the severity anchors and the last-decision-point fix) is adapted from the MIT-licensed `security-audit` skill in <https://github.com/cloudflare/security-audit-skill> (commit `c1c8a8c`), which is curated whole for full codebase audits. Its audit workflow, findings schema and attack-class companions are not carried over.

Several rules are ideas from the Elephant-Goldfish Model, <https://github.com/google/elephant-goldfish-model> (Apache-2.0), reworded; no text is carried over:

- the paraphrase that opens the Spec lens, from its comprehension reviewer
- the search for an existing helper in the Duplicated Code smell, from its zoom-out reviewer
- reporting a review sub-agent that fails twice as not reviewed rather than clean, from its synthesizer
- rejecting a finding only with evidence a reader can open (*Weigh and disagree* in `LENSES.md`), from its resolve skill

---

MIT License

Copyright (c) 2026 Matt Pocock
Copyright (c) 2025-2026 Cloudflare, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
