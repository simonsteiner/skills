"""A stand-in for the `gh` CLI, so the scripts bundled in skills run without a network.

The scripts call `gh` by name; FakeGh puts this one first on PATH. It answers from a
list of rules, logs every call, and fails any call no rule matches, so a test also
proves what a script did *not* send.

A rule: {"args": [...prefix of argv...], "stdout": "text" | "json": <value>, "exit": 0,
"once": false}. With "json" and a `--jq` in argv, the filter runs through the real jq
(strings raw, everything else compact JSON, as gh prints them), with the caller's
environment, so `env.X` filters work as they do under gh.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()


class FakeGh:
    def __init__(self, tmp):
        self.dir = Path(tmp)
        self.rules, self.spec, self.log = [], self.dir / "gh-rules.json", self.dir / "gh-calls.jsonl"
        bin_dir = self.dir / "bin"
        bin_dir.mkdir()
        shim = bin_dir / "gh"
        shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" -I "{HERE}" "$@"\n')
        shim.chmod(0o755)
        self.path = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"

    def on(self, *args, **rule):
        self.rules.append({"args": list(args), **rule})
        return self

    def run(self, script, *args, stdin="", env=None):
        self.spec.write_text(json.dumps(self.rules))
        self.log.write_text("")
        env = {**os.environ, "PATH": self.path, "FAKE_GH_RULES": str(self.spec),
               "FAKE_GH_LOG": str(self.log), **(env or {})}
        return subprocess.run([str(script), *map(str, args)], input=stdin, capture_output=True,
                              text=True, env=env, check=False)

    @property
    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]


def main(argv):
    rules_path = Path(os.environ["FAKE_GH_RULES"])
    rules = json.loads(rules_path.read_text())
    stdin = "" if sys.stdin.isatty() else sys.stdin.read() if "--input" in argv else ""
    with open(os.environ["FAKE_GH_LOG"], "a") as log:
        log.write(json.dumps({"args": argv, "stdin": stdin}) + "\n")
    for i, rule in enumerate(rules):
        if argv[: len(rule["args"])] != rule["args"]:
            continue
        if rule.get("once"):
            rules.pop(i)
            rules_path.write_text(json.dumps(rules))
        out = rule.get("stdout", "")
        if "json" in rule:
            out = json.dumps(rule["json"])
            if "--jq" in argv:
                jq = argv[argv.index("--jq") + 1]
                out = subprocess.run(["jq", "-r", "-c", jq], input=out, capture_output=True, text=True, check=True).stdout
        sys.stdout.write(out)
        return rule.get("exit", 0)
    sys.stderr.write(f"fake gh: no rule for {argv}\n")
    return 99


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
