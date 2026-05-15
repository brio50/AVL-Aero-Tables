"""Pytest configuration: req marker hooks and terminal coverage summary."""

from __future__ import annotations

from collections import defaultdict

import pytest

_req_outcomes: dict[str, list[str]] = defaultdict(list)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:  # type: ignore[type-arg]
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        for marker in item.iter_markers("req"):
            for req_id in marker.args:
                _req_outcomes[req_id].append(report.outcome)


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    if not _req_outcomes:
        return
    passed = sorted(
        r for r, oc in _req_outcomes.items() if all(o == "passed" for o in oc)
    )
    failed = sorted(
        r for r, oc in _req_outcomes.items() if any(o != "passed" for o in oc)
    )
    terminalreporter.write_sep("-", "requirement coverage")
    for r in failed:
        terminalreporter.write_line(f"  FAIL  {r}", red=True)
    total = len(_req_outcomes)
    terminalreporter.write_line(
        f"  {total} covered · {len(passed)} passed · {len(failed)} failed",
        green=not failed,
        red=bool(failed),
    )
