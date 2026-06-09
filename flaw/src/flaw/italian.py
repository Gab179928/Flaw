import argparse
import sqlite3
import time
from pathlib import Path

from . import core


def show_header() -> None:
    lines = [
        f"{core.ORANGE}{core.read_banner()}{core.RESET}",
        f"{core.ORANGE}Flaw — motore di ricerca password professionale per grandi archivi.{core.RESET}",
        f"{core.ORANGE}Versione 1.0 | Interfaccia a riga comandi migliorata{core.RESET}",
        "Supporta ricerca singola, batch, contenuto, prefisso, suffisso e regex.",
        "Usa solo database SQLite indicizzati.",
        "Risultati stampati con effetto macchina da scrivere.",
    ]
    core.typewriter_print(lines)


def create_parser() -> argparse.ArgumentParser:
    description = (
        "Flaw è uno strumento avanzato per cercare password in archivi grandi. "
        "Usa solo database SQLite indicizzati, senza scansione diretta di file compressi."
    )
    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=formatter,
        epilog=(
            "Esempi:\n"
            "  python main.py --search password123\n"
            "  python main.py --contains secret --ignore-case\n"
            "  python main.py --batch wordlist.txt --output results.txt\n"
            "  python main.py --regex '^admin.*'\n"
            "  python main.py --stats\n"
            "  python main.py --interactive"
        ),
    )
    parser.add_argument("--interactive", action="store_true", help="Avvia la modalità interattiva in italiano")
    parser.add_argument("--search", metavar="PASSWORD", help="Cerca una password specifica")
    parser.add_argument("--batch", metavar="FILE", help="Cerca un elenco di password, una per riga")
    parser.add_argument("--contains", metavar="SUBSTRING", help="Trova password che contengono la stringa fornita")
    parser.add_argument("--prefix", metavar="PREFIX", help="Trova password che iniziano con il prefisso")
    parser.add_argument("--suffix", metavar="SUFFIX", help="Trova password che finiscono con il suffisso")
    parser.add_argument("--regex", metavar="PATTERN", help="Trova password che corrispondono alla regex fornita")
    parser.add_argument("--stats", action="store_true", help="Mostra informazioni sul database disponibile")
    parser.add_argument("--duplicates", action="store_true", help="Mostra password duplicate normalizzate")
    parser.add_argument("--ignore-case", action="store_true", help="Ignora maiuscole/minuscole")
    parser.add_argument("--normalize", action="store_true", help="Normalizza le password rimuovendo caratteri non stampabili")
    parser.add_argument("--output", metavar="FILE", help="Salva i risultati su un file di testo")
    parser.add_argument("--limit", type=int, default=20, help="Numero massimo di risultati da mostrare")
    return parser


def show_stats(db_path: Path | None) -> None:
    if db_path is None:
        core.typewriter_print(["Errore: database non trovato. Posiziona rockyou_opt.db o rockyou.db nella cartella."])
        return
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM passwords")
            total = cursor.fetchone()[0]
            lines = [
                "=== STATISTICHE FLOWSCAN ===",
                f"Database: {db_path}",
                f"Record indicizzati: {total}",
                f"Indice normalizzato: {'sì' if core.database_has_normalized_field(db_path) else 'no'}",
                "============================",
            ]
            core.typewriter_print(lines)
    except sqlite3.Error:
        core.typewriter_print(["Errore: impossibile leggere il database SQLite."])


def show_duplicates(db_path: Path | None, limit: int) -> None:
    if db_path is None:
        core.typewriter_print(["Errore: database non trovato. Non è possibile analizzare i duplicati."])
        return
    try:
        with sqlite3.connect(db_path) as conn:
            if not core.database_has_normalized_field(db_path):
                core.typewriter_print(["Errore: il database non contiene il campo normalized."])
                return
            cursor = conn.cursor()
            cursor.execute(
                "SELECT normalized, COUNT(*) AS cnt FROM passwords GROUP BY normalized HAVING cnt > 1 ORDER BY cnt DESC LIMIT ?",
                (limit,),
            )
            duplicates = cursor.fetchall()
            if not duplicates:
                core.typewriter_print(["Nessun duplicato normalizzato trovato."])
                return
            lines = [f"Duplicati trovati: {len(duplicates)} (fino a {limit})"]
            lines += [f"{value} ({count} occorrenze)" for value, count in duplicates]
            core.typewriter_print(lines)
    except sqlite3.Error:
        core.typewriter_print(["Errore: impossibile leggere il database per i duplicati."])


def process_command(command: str, db_path: Path | None, ignore_case: bool, normalize: bool) -> None:
    if not command:
        return
    if command.lower() in {"quit", "exit", "q"}:
        core.typewriter_print(["Uscita dalla modalità interattiva."])
        raise KeyboardInterrupt
    if command.lower() == "stats":
        show_stats(db_path)
        return
    if command.lower() == "duplicates":
        show_duplicates(db_path, limit=20)
        return
    if command.lower() == "help":
        core.typewriter_print(["Comandi: stats, duplicates, help, quit. Oppure digita una password."])
        return
    if command.lower().startswith("contains "):
        _, term = command.split(" ", 1)
        results = core.search_database_pattern(term, db_path, "contains", ignore_case)
        lines = [f"Risultati contains: {len(results)}"] + [f"{line}: {core.GREEN}{pwd}{core.RESET}" for pwd, line in results[:20]]
        core.typewriter_print(lines if lines else ["Nessun risultato."])
        return
    if db_path is None:
        core.typewriter_print(["Errore: database non trovato. Impossibile cercare la password."])
        return
    start_time = time.time()
    search_value = core.normalize_password(command) if normalize else command
    line_number = core.search_database_exact(search_value, db_path, ignore_case=ignore_case)
    duration = time.time() - start_time
    if line_number is not None:
        core.typewriter_print([f"✅ {core.GREEN}Trovata alla riga {line_number}: {command}{core.RESET}", f"⏱ Esecuzione: {duration:.6f} secondi"])
    else:
        core.typewriter_print([f"❌ La password '{command}' NON è nella lista.", f"⏱ Esecuzione: {duration:.6f} secondi"])


def interactive_mode(db_path: Path | None) -> None:
    core.typewriter_print(["Modalità interattiva avviata. Digita 'help' per i comandi disponibili."])
    while True:
        try:
            command = input("flaw> ").strip()
            process_command(command, db_path, ignore_case=True, normalize=True)
        except KeyboardInterrupt:
            core.typewriter_print(["\nUscita dalla modalità interattiva."])
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
        core.typewriter_print(["Errore: database non trovato. Posiziona rockyou_opt.db o rockyou.db nella cartella."])
        return
    if args.search:
        start_time = time.time()
        search_value = core.normalize_password(args.search) if args.normalize else args.search
        line_number = core.search_database_exact(search_value, db_path, ignore_case=args.ignore_case)
        output = [f"✅ {core.GREEN}Trovata alla riga {line_number}: {args.search}{core.RESET}"] if line_number is not None else [f"❌ La password '{args.search}' NON è nella lista."]
        output.append(f"⏱ Esecuzione: {time.time() - start_time:.6f} secondi")
    elif args.batch:
        if not Path(args.batch).exists():
            core.typewriter_print([f"Errore: file batch non trovato: {args.batch}"])
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
                    output.append(f"✅ {core.GREEN}{item}{core.RESET} -> riga {line_number}")
                else:
                    output.append(f"❌ {item} NON trovato")
    elif args.contains or args.prefix or args.suffix or args.regex:
        if args.regex:
            try:
                results = core.search_database_regex(args.regex, db_path, ignore_case=args.ignore_case)
            except ValueError as exc:
                core.typewriter_print([f"Errore regex: {exc}"])
                return
            output = [f"🔍 Risultati regex: {len(results)}"] + [f"{line}: {core.GREEN}{pwd}{core.RESET}" for pwd, line in results[: args.limit]]
        else:
            mode = "contains" if args.contains else "prefix" if args.prefix else "suffix"
            term = args.contains or args.prefix or args.suffix
            results = core.search_database_pattern(term, db_path, mode, ignore_case=args.ignore_case)
            output = [f"🔍 Risultati {mode}: {len(results)}"] + [f"{line}: {core.GREEN}{pwd}{core.RESET}" for pwd, line in results[: args.limit]]
    else:
        parser.print_help()
        return
    if args.output:
        core.write_output(Path(args.output), output)
    else:
        core.typewriter_print(output)
