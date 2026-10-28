#!/usr/bin/env python3
"""Run validate_week.py over every file in tests/weeks/ and assert expected exit codes.

Mapping: each file's expected exit code is defined here. The runner also
collects and reports any unexpected output lines for diagnosis.
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
VALIDATOR = BASE / "tools" / "validate_week.py"
WEEKS_DIR = BASE / "tests" / "weeks"

# file stem -> expected exit code
EXPECTED: dict[str, int] = {
    "good_week": 0,
    "bad_two_trip": 1,
    "bad_no_day1": 1,
    "bad_no_serve_day": 1,
    "bad_disjoint_pool": 1,
    "bad_overlap_claim": 1,
    "bad_single_cuisine": 1,
    "bad_too_few_cuisines": 1,
}

# Which constraint failure each bad file should trigger
MUST_CONTAIN: dict[str, list[str]] = {
    "bad_two_trip": ["C1 FAIL"],
    "bad_no_day1": ["C2 FAIL"],
    "bad_no_serve_day": ["C3 FAIL"],
    "bad_disjoint_pool": ["C5 FAIL"],
    "bad_overlap_claim": ["C4b FAIL"],
    "bad_single_cuisine": ["C5 FAIL"],
    "bad_too_few_cuisines": ["C5 FAIL"],
}


def run_test(stem: str) -> dict:
    file_path = WEEKS_DIR / f"{stem}.json"
    if not file_path.exists():
        return {"stem": stem, "exit_code": -1, "stdout": "", "passed": False, "error": f"File not found: {file_path}"}

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(file_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    expected = EXPECTED.get(stem, 0)
    exit_ok = result.returncode == expected
    output = result.stdout + result.stderr

    # Check constraint-failure content for bad files
    content_ok = True
    content_errors = []
    if stem in MUST_CONTAIN and expected != 0:
        for phrase in MUST_CONTAIN[stem]:
            if phrase not in output:
                content_ok = False
                content_errors.append(f"Missing expected failure phrase: {phrase!r}")

    # Good files should not print FAILURES
    if expected == 0 and "FAIL" in output:
        exit_ok = False
        content_errors.append("Good file triggered a FAIL output")

    passed = exit_ok and content_ok
    return {
        "stem": stem,
        "exit_code": result.returncode,
        "expected": expected,
        "stdout": output.strip(),
        "passed": passed,
        "content_errors": content_errors,
        "exit_ok": exit_ok,
    }


def main():
    results = []
    for stem in EXPECTED:
        results.append(run_test(stem))

    print("=" * 70)
    print("VALIDATOR TEST RUNNER")
    print("=" * 70)

    all_passed = True
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_passed = False
        print(f"\n--- {r['stem']}: {status} ---")
        print(f"  exit: got {r['exit_code']}, expected {r['expected']} "
              f"({'✓' if r['exit_ok'] else '✗'})")
        if r.get("content_errors"):
            for ce in r["content_errors"]:
                print(f"  content: ✗ {ce}")
        if r["stdout"]:
            for line in r["stdout"].split("\n"):
                print(f"  | {line}"[:200])

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()