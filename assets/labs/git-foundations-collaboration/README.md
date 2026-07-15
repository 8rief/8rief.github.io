# Git foundations and collaboration lab

This local lab supports the Git foundations teaching package. It creates a controlled Git repository, records working-tree/index/commit evidence, inspects objects and refs, reproduces a merge conflict, demonstrates a local rebase boundary, uses a local bare remote, simulates a colleague clone, creates a release tag, and writes Markdown/JSON evidence.

Run:

```bash
./run_lab.sh
```

Artifacts:

- `reports/transcript.txt`: command transcript.
- `reports/git_foundations_report.md`: human-readable evidence report.
- `reports/observations.json`: machine-readable observations.
- `workspace/`: local-only Git repositories created by the lab.

The lab does not contact a network remote and does not modify any existing repository.
