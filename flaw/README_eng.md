Flaw — Password search utility

Overview

Flaw is a command-line tool for searching password archives using an optimized SQLite database. The main version `flaw.py` is Italian, while `flaw_eng.py` is English.

Quick start

- Search for a password:

  python main_eng.py --search password123

- Search for a substring (case-insensitive):

  python main_eng.py --contains secret --ignore-case

- Start interactive mode:

  python main_eng.py --interactive

Notes

- Results are printed with a typewriter effect.
- The required database is `rockyou_opt.db` or `rockyou.db`.
- Use `python main_eng.py` or `python flaw_eng.py` to start the English tool.
- Requirements and installation instructions are available in `installazione.md` or `install.txt`.
- The main code lives in `src/flaw/`.
- A small amount of AI assistance was used during development.

Files in this folder:
- `main.py` (Italian entry point)
- `main_eng.py` (English entry point)
- `flaw.py` (Italian compatibility wrapper)
- `flaw_eng.py` (English compatibility wrapper)
- `README.md` (Italian documentation)
- `README_eng.md` (English documentation)
- `LICENSE` (Italian license)
- `LICENSE_eng` (English license)
- `ascii.txt` (ASCII banner)
- `src/flaw/` (package source code)
- `rockyou_opt.db` (optional optimized database)
