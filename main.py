# main.py (aktualisierte Version)

import logging
import sys
from pathlib import Path
from src.main_logic import FiindoChallenge
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Hauptfunktion der Anwendung"""
    logger.info("=" * 50)
    logger.info("Fiindo Challenge Application gestartet")
    logger.info("=" * 50)

    # Hauptlogik ausführen
    challenge = FiindoChallenge()
    challenge.run()

    logger.info("Anwendung beendet")


if __name__ == "__main__":
    # Sicherstellen, dass Verzeichnisse existieren
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    try:
        main()
    except KeyboardInterrupt:
        logger.info("Anwendung durch Benutzer beendet")
    except Exception as e:
        logger.error(f"Fehler in der Anwendung: {e}", exc_info=True)
        sys.exit(1)