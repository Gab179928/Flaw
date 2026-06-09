import argparse
import sqlite3
import time
from pathlib import Path

from . import core


def show_header() -> None:
    lines = [
        f"{core.ORANGE}{core.read_banner()}{core.RESET}",
        f"{core.ORANGE}Flaw — professional password search engine for large archives.{core.RESET}",
        f"{core.ORANGE}Versione 1.0 | Improved command line interface{core.RESET}",
        "Supports single search, batch, contains, prefix, suffix and regex.",
        "Uses SQLite database when available.",
        "Results are printed with a typewriter effect.",
    ]
    core.typewriter_print(lines)


def create_parser() -> argparse.ArgumentParser:
    description = (
        "Flaw is a powerful tool for searching password archives. "
        "It uses only SQLite indexes and does not scan compressed archives directly."
    )
    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=formatter,
        epilog=(
            "Examples:\n"
            "  python main_eng.py --search password123\n"
            "  python main_eng.py --contains secret --ignore-case\n"
            "  python main_eng.py --batch wordlist.txt --output results.txt\n"
            "  python main_eng.py --regex '^admin.*'\n"
            "  python main_eng.py --stats\n"
            "  python main_eng.py --interactive"
        ),
    )
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode in English")
    parser.add_argument("--search", metavar="PASSWORD", help="Search for a specific password")
    parser.add_argument("--batch", metavar="FILE", help="Search a list of passwords, one per line")
    parser.add_argument("--contains", metavar="SUBSTRING", help="Find passwords containing the supplied substring")
    parser.add_argument("--prefix", metavar="PREFIX", help="Find passwords starting with the supplied prefix")
    parser.add_argument("--suffix", metavar="SUFFIX", help="Find passwords ending with the supplied suffix")
    parser.add_argument("--regex", metavar="PATTERN", help="Find passwords matching the supplied regex")
    parser.add_argument("--stats", action="store_true", help="Show database information")
    parser.add_argument("--duplicates", action="store_true", help="Show normalized duplicate passwords")
    parser.add_argument("--ignore-case", action="store_true", help="Ignore case in searches")
    parser.add_argument("--normalize", action="store_true", help="Normalize passwords by removing nonprintable characters")
    parser.add_argument("--output", metavar="FILE", help="Save results to a text file")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of results to show")
    return parser


def show_stats(db_path: Path | None) -> None:
    if db_path is None:
        core.typewriter_print(["Error: database not found. Place rockyou_opt.db or rockyou.db in the folder."])
        return
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM passwords")
            total = cursor.fetchone()[0]
            lines = [
                "=== FLOWSCAN STATS ===",
                f"Database: {db_path}",
                f"Indexed rows: {total}",
                f"Normalized index: {'yes' if core.database_has_normalized_field(db_path) else 'no'}",
                "======================",
            ]
            core.typewriter_print(lines)
    except sqlite3.Error:
        core.typewriter_print(["Error: unable to read the SQLite database."])


def show_duplicates(db_path: Path | None, limit: int) -> None:
    if db_path is None:
        core.typewriter_print(["Error: database not found. Cannot analyze duplicates."])
        return
    try:
        with sqlite3.connect(db_path) as conn:
            if not core.database_has_normalized_field(db_path):
                core.typewriter_print(["Error: the database does not include the normalized field."])
                return
            cursor = conn.cursor()
            cursor.execute(
                "SELECT normalized, COUNT(*) AS cnt FROM passwords GROUP BY normalized HAVING cnt > 1 ORDER BY cnt DESC LIMIT ?",
                (limit,),
            )
            duplicates = cursor.fetchall()
            if not duplicates:
                core.typewriter_print(["No normalized duplicates found."])
                return
            lines = [f"Duplicates found: {len(duplicates)} (up to {limit})"]
            lines += [f"{value} ({count} occurrences)" for value, count in duplicates]
            core.typewriter_print(lines)
    except sqlite3.Error:
        core.typewriter_print(["Error: unable to read the database for duplicates."])


def process_command(command: str, db_path: Path | None, ignore_case: bool, normalize: bool) -> None:
    if not command:
        return
    if command.lower() in {"quit", "exit", "q"}:
        core.typewriter_print(["Exiting interactive mode."])
        raise KeyboardInterrupt
    if command.lower() == "stats":
        show_stats(db_path)
        return
    if command.lower() == "duplicates":
        show_duplicates(db_path, limit=20)
        return
    if command.lower() == "help":
        core.typewriter_print(["Commands: stats, duplicates, help, quit. Or type a password to search."])
        return
    if command.lower().startswith("contains "):
        _, term = command.split(" ", 1)
        results = core.search_database_pattern(term, db_path, "contains", ignore_case)
        lines = [f"Contains results: {len(results)}"] + [f"{line}: {core.GREEN}{pwd}{core.RESET}" for pwd, line in results[:20]]
        core.typewriter_print(lines if lines else ["No results."])
        return
    if db_path is None:
        core.typewriter_print(["Error: database not found. Cannot search."])
        return
    start_time = time.time()
    search_value = core.normalize_password(command) if normalize else command
    line_number = core.search_database_exact(search_value, db_path, ignore_case=ignore_case)
    duration = time.time() - start_time
    if line_number is not None:
        core.typewriter_print([f"✅ {core.GREEN}Found at line {line_number}: {command}{core.RESET}", f"⏱ Duration: {duration:.6f} seconds"])
    else:
        core.typewriter_print([f"❌ Password '{command}' not found.", f"⏱ Duration: {duration:.6f} seconds"])


def interactive_mode(db_path: Path | None) -> None:
    core.typewriter_print(["Interactive mode started. Type 'help' for commands."])
    while True:
        try:
            command = input("flaw> ").strip()
            process_command(command, db_path, ignore_case=True, normalize=True)
        except KeyboardInterrupt:
            core.typewriter_print(["\nExiting interactive mode."])
            break


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    show_header()
    db_path = core.get_database_path()
    if args.stats:
        show_stats(db_path)
        return
    if args.duplicates:
        show_duplicates(db_path, limit=args.limit)
        return
    if args.interactive:
        interactive_mode(db_path)
        return
    if db_path is None:
        core.typewriter_print(["Error: database not found. Place rockyou_opt.db or rockyou.db in the folder."])
        return
    if args.search:
        start_time = time.time()
        search_value = core.normalize_password(args.search) if args.normalize else args.search
        line_number = core.search_database_exact(search_value, db_path, ignore_case=args.ignore_case)
        output = [f"✅ {core.GREEN}Found at line {line_number}: {args.search}{core.RESET}"] if line_number is not None else [f"❌ Password '{args.search}' not found."]
        output.append(f"⏱ Duration: {time.time() - start_time:.6f} seconds")
    elif args.batch:
        if not Path(args.batch).exists():
            core.typewriter_print([f"Error: batch file not found: {args.batch}"])
            return
        output = []
        with Path(args.batch).open("r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                item = raw.strip()
                if not item:
                    continue
                search_value = core.normalize_password(item) if args.normalize else item
                line_number = core.search_database_exact(search_value, db_path, ignore_case=args.ignore_case)
                if line_number is not None:
                    output.append(f"✅ {core.GREEN}{item}{core.RESET} -> line {line_number}")
                else:
                    output.append(f"❌ {item} not found")
    elif args.contains or args.prefix or args.suffix or args.regex:
        if args.regex:
            try:
                results = core.search_database_regex(args.regex, db_path, ignore_case=args.ignore_case)
            except ValueError as exc:
                core.typewriter_print([f"Error regex: {exc}"])
                return
            output = [f"🔍 Regex results: {len(results)}"] + [f"{line}: {core.GREEN}{pwd}{core.RESET}" for pwd, line in results[: args.limit]]
        else:
            mode = "contains" if args.contains else "prefix" if args.prefix else "suffix"
            term = args.contains or args.prefix or args.suffix
            results = core.search_database_pattern(term, db_path, mode, ignore_case=args.ignore_case)
            output = [f"🔍 {mode.capitalize()} results: {len(results)}"] + [f"{line}: {core.GREEN}{pwd}{core.RESET}" for pwd, line in results[: args.limit]]
    else:
        parser.print_help()
        return
    if args.output:
        core.write_output(Path(args.output), output)
    else:
        core.typewriter_print(output)
