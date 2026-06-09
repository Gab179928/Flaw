from pathlib import Path
import sys

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "src"))

from flaw.italian import main

if __name__ == "__main__":
    main()
