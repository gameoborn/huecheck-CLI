"""Print intentionally ambiguous, low-contrast terminal output."""
print("\033[31mERROR: request failed\033[0m")
print("\033[32mSUCCESS: request completed\033[0m")
print("\033[90mThis dim text may disappear on a dark background.\033[0m")
