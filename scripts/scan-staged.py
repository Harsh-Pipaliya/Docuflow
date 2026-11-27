"""Check staged additions without printing their contents."""
import re
import subprocess
import sys

patterns = [
    rb"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----",
    rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
    rb"gh[pousr]_[A-Za-z0-9]{30,}",
    rb"github_pat_[A-Za-z0-9_]{30,}",
    rb"(?i)^\+\s*(?:DEMO_PASSWORD(?:_HASH)?|SESSION_SECRET|API_KEY)\s*=\s*\S+",
]
diff = subprocess.check_output(["git", "diff", "--cached", "--no-ext-diff",
                                "--no-textconv", "--unified=0", "--diff-filter=ACMR"])
for line in diff.splitlines():
    if line.startswith(b"+") and any(re.search(pattern, line) for pattern in patterns):
        sys.exit("Possible credential in staged changes. Inspect the staged diff locally.")
