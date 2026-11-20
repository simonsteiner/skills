# Credits

The idea of this skill comes from the Elephant-Goldfish Model, <https://github.com/google/elephant-goldfish-model> (Apache-2.0), and Dave Rensin's essay behind it: a document is drafted by an agent that holds the context and reviewed by fresh agents that see only the document and the code.

Several rules are its ideas, reworded; no text is carried over:

- the paraphrase-first comprehension check, from its comprehension reviewer
- the reuse search and speculation checks in the Simplicity lens, from its zoom-out reviewer and standard
- the zero-decisions rule and the false-claims-about-current-code check in the Readiness lens, from its implementation-readiness and codebase-details reviewers
- the evidence rules for contesting a finding, from its resolve skill
- the settled list, clean rounds, two-round convergence, five-round cap and churn rule, from its review-loop skill
- counting a failed reviewer as not run rather than as clean, from its synthesizer
