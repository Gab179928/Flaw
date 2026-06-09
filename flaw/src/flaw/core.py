import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path

ASCII_BANNER_PATH = Path("ascii.txt")
OPT_DB_PATH = Path("rockyou_opt.db")
LEGACY_DB_PATH = Path("rockyou.db")
ORANGE = "\x1b[38;5;208m"
GREEN = "\x1b[32m"
RESET = "\x1b[0m"
LINE_DELAY = 0.03
WORD_DELAY = 0.02


def read_banner() -> str:
    if ASCII_BANNER_PATH.exists():
        return ASCII_BANNER_PATH.read_text(encoding="utf-8", errors="ignore")
    return "FLAW"


def get_database_path() -> Path | None:
    if OPT_DB_PATH.exists():
        return OPT_DB_PATH
    if LEGACY_DB_PATH.exists():
        return LEGACY_DB_PATH
    return None


def typewriter_line(line: str) -> None:
    words = line.split()
    for index, word in enumerate(words):
        sys.stdout.write(word)
        if index < len(words) - 1:
            sys.stdout.write(" ")
        sys.stdout.flush()
        time.sleep(WORD_DELAY)
    sys.stdout.write("\n")
    sys.stdout.flush()


def typewriter_print(lines: list[str]) -> None:
    if len(lines) == 1:
        typewriter_line(lines[0])
        return
    for line in lines:
        print(line)
        time.sleep(LINE_DELAY)


def normalize_password(password: str) -> str:
    return "".join(ch for ch in password.strip() if ch.isprintable())


def database_has_normalized_field(db_path: Path) -> bool:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(passwords)")
            return any(row[1] == "normalized" for row in cursor.fetchall())
    except sqlite3.Error:
        return False


def search_database_exact(password: str, db_path: Path, ignore_case: bool = False) -> int | None:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            clause = "COLLATE NOCASE" if ignore_case else ""
            cursor.execute(
                f"SELECT line_number FROM passwords WHERE password = ? {clause} LIMIT 1",
                (password,),
            )
            row = cursor.fetchone()
            if row is not None:
                return row[0]
            if database_has_normalized_field(db_path):
                normalized = normalize_password(password)
                cursor.execute(
                    f"SELECT line_number FROM passwords WHERE normalized = ? {clause} LIMIT 1",
                    (normalized,),
                )
                row = cursor.fetchone()
                return row[0] if row is not None else None
    except sqlite3.Error:
        return None
    return None


def search_database_pattern(pattern: str, db_path: Path, mode: str, ignore_case: bool) -> list[tuple[str, int]]:
    value = {
        "contains": f"%{pattern}%",
        "prefix": f"{pattern}%",
        "suffix": f"%{pattern}",
    }.get(mode, pattern)
    collate = " COLLATE NOCASE" if ignore_case else ""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT password, line_number FROM passwords WHERE password LIKE ?{collate} ORDER BY line_number LIMIT 100",
                (value,),
            )
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def search_database_regex(pattern: str, db_path: Path, ignore_case: bool = False) -> list[tuple[str, int]]:
    try:
        flags = re.IGNORECASE if ignore_case else 0
        compiled = re.compile(pattern, flags)

        def regexp(expr: str, item: str) -> bool:
            return compiled.search(item) is not None

        with sqlite3.connect(db_path) as conn:
            conn.create_function("REGEXP", 2, regexp)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password, line_number FROM passwords WHERE password REGEXP ? ORDER BY line_number LIMIT 100",
                (pattern,),
            )
            return cursor.fetchall()
    except re.error:
        raise ValueError("Invalid regular expression")
    except sqlite3.Error:
        return []


def write_output(output_path: Path, lines: list[str]) -> None:
    try:
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        typewriter_print([f"✅ Results saved to: {output_path}"])
    except OSError as exc:
        typewriter_print([f"Error: unable to write to {output_path}: {exc}"])
