# huecheck CLI

`huecheck` runs a command in a pseudo-terminal, captures its raw ANSI output, and checks foreground/background contrast across 21 bundled terminal themes. It can also inspect an ANSI capture saved to disk. A self-contained HTML report renders the captured output in each theme and marks low-contrast spans with a wavy underline.

Requires Python 3.10+. Runtime uses only the standard library; pytest is used for tests.

## Install

```sh
python -m pip install -e .
```

## Examples

```sh
huecheck run -- python demo/failing_program.py
huecheck ci --min-contrast 4.5 -- python demo/failing_program.py
huecheck file huecheck-capture.ansi
```

`run` and `ci` write `huecheck-capture.ansi` and `huecheck-report.html` in the current directory. Use `--report PATH` to select another HTML destination. The `ci` command exits 1 when any theme contains a contrast failure or the simulated color-vision check finds a potentially confusable pair.

## Checks and limits

Contrast uses the WCAG relative-luminance formula. ANSI 16-color codes resolve through each theme; 256-color and truecolor codes retain their specified RGB values. Default foreground and background resolve from each theme. Bold and reverse video are applied in the report and contrast check.

Color vision simulation uses standard approximate linear RGB matrices for protanopia, deuteranopia, and tritanopia. Pair comparison uses deltaE76 in CIE Lab with a default threshold of 10. Since raw terminal output has no semantic labels, huecheck compares differently worded text runs as candidate meanings; review these warnings in context. It does not interpret cursor movement, screen clearing, images, or dynamic TUI repaint behavior.

The PTY runner currently targets POSIX systems. Child stdout and stderr are merged into the capture. The command's exit status is not used as the CI result; CI status indicates accessibility findings.

## Tests

```sh
python -m pytest
```
