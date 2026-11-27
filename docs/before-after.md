# Before and after

| Scenario | Frozen harness | Implemented workflow | Evidence |
|---|---|---|---|
| Valid synthetic PDF | Processed without parsing | Four stages and page count recorded | after/event-trace.json |
| Wrong extension | Rejected | 415 before any worker invocation | after/matrix.md |
| Oversized | 10,485,761 bytes accepted | 413 and unchanged record count | after/test-results.json |
| Replay | Side effect count reached two | Complete record and history snapshots remained equal | after/replay.json |
| Worker failure | Stuck in Validating | Failed with controlled code, log and history | after/forced-failure.txt |
| Storage identity | Harness tracked bytes in memory | Separate generated keys; filename only for display | after/security.json |

Paths in the evidence column are relative to evidence/. The frozen results are in evidence/baseline/results.jsonl.
