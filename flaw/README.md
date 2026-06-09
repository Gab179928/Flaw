Flaw — Utility di ricerca password

Panoramica

Flaw è uno strumento da riga di comando per cercare archivi di password usando un database SQLite ottimizzato. La versione principale `flaw.py` mostra messaggi in italiano.

Esempi rapidi

- Cerca una password singola:

  python main.py --search password123

- Cerca una sottostringa (case-insensitive):

  python main.py --contains secret --ignore-case

- Avvia la modalità interattiva:

  python main.py --interactive

Note

- I risultati vengono stampati con un effetto macchina da scrivere.
- Il database richiesto è `rockyou_opt.db` o `rockyou.db`.
- Usa `python main.py` o `python flaw.py` per avviare il tool in italiano.
- Requisiti e istruzioni di installazione sono disponibili in `installazione.md` o `install.txt`.
- Il codice principale è organizzato in `src/flaw/`.
- Un po', ma poco, è stata usata l'AI durante lo sviluppo.

File nella cartella:
- `main.py` (entry point italiano)
- `main_eng.py` (entry point inglese)
- `flaw.py` (compatibilità con il pacchetto italiano)
- `flaw_eng.py` (compatibilità con il pacchetto inglese)
- `README.md` (documentazione in italiano)
- `README_eng.md` (documentazione in inglese)
- `LICENSE` (licenza in italiano)
- `LICENSE_eng` (licenza in inglese)
- `ascii.txt` (banner ASCII)
- `src/flaw/` (codice sorgente del pacchetto)
- `rockyou_opt.db` (database opzionale ottimizzato)
