# Debug and Build Tooling Foundations Lab

A C++20 lab for practical debugging and build tooling. It covers warnings-as-errors, CMake/Ninja target inspection, CTest regression tests, sanitizer evidence, minimal reproduction, logging, timing, and symbol inspection.

Run:

```bash
bash run_lab.sh
```

Generated artifacts:

- `reports/transcript.txt`: full transcript.
- `reports/test_output.txt`: CTest output.
- `reports/sanitizer_output.txt`: ASan/UBSan evidence.
- `reports/timing_output.txt`: timing output.
- `reports/build_targets.txt`: Ninja target list.
- `reports/symbol_output.txt`: nm/addr2line evidence.
- `reports/debug_build_report.md`: human-readable report.
- `.lab_tmp/`: generated build directories, recreated by `run_lab.sh` and removable after validation.
