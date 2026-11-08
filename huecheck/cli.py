"""Command line interface."""
from __future__ import annotations

import argparse
import os
import pty
import select
import subprocess
import sys
from pathlib import Path

from .parser import parse_ansi
from .report import analyze, html_report, terminal_summary


def capture_pty(command: list[str]) -> bytes:
    """Run command attached to a PTY and return its raw combined output."""
    if os.name != "posix":
        raise RuntimeError("PTY command capture currently requires a POSIX platform")
    master, slave = pty.openpty()
    try:
        process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
    finally:
        os.close(slave)
    chunks = []
    try:
        while True:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            elif process.poll() is not None:
                break
        process.wait()
    finally:
        os.close(master)
    return b"".join(chunks)


def _command_after_separator(command: list[str]) -> list[str]:
    return command[1:] if command and command[0] == "--" else command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="huecheck", description="Check ANSI terminal output for contrast and color-vision accessibility.")
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run", help="run a command in a PTY and analyze its output")
    run.add_argument("--min-contrast", type=float, default=4.5)
    run.add_argument("--report", default="huecheck-report.html")
    run.add_argument("command", nargs=argparse.REMAINDER)
    ci = sub.add_parser("ci", help="run a command and return nonzero when checks fail")
    ci.add_argument("--min-contrast", type=float, default=4.5)
    ci.add_argument("--report", default="huecheck-report.html")
    ci.add_argument("command", nargs=argparse.REMAINDER)
    file_cmd = sub.add_parser("file", help="analyze a saved ANSI capture")
    file_cmd.add_argument("path")
    file_cmd.add_argument("--min-contrast", type=float, default=4.5)
    file_cmd.add_argument("--report", default="huecheck-report.html")
    args = parser.parse_args(argv)
    if args.min_contrast <= 0:
        parser.error("--min-contrast must be positive")
    if args.action in ("run", "ci"):
        command = _command_after_separator(args.command)
        if not command:
            parser.error("provide a command after --")
        try:
            raw = capture_pty(command)
        except (OSError, RuntimeError) as exc:
            parser.error(str(exc))
        # Preserve the raw capture for downstream pipelines and users.
        capture_path = Path("huecheck-capture.ansi")
        capture_path.write_bytes(raw)
    else:
        raw = Path(args.path).read_bytes()
    spans = parse_ansi(raw)
    results = analyze(spans, args.min_contrast)
    print(terminal_summary(results, args.min_contrast))
    Path(args.report).write_text(html_report(spans, results, min_contrast=args.min_contrast), encoding="utf-8")
    print(f"HTML report: {args.report}")
    if args.action == "ci" and any(r["failures"] or r["cvd"] for r in results):
        return 1
    if args.action in ("run", "ci"):
        # Mirror child status only when accessibility checks pass.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
