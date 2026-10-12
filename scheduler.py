"""
Scheduler — Exécution automatique du pipeline

Ce script permet de planifier l'exécution du pipeline à intervales réguliers.
Il peut être utilise avec cron (Linux/Mac) ou le Planificateur de taches (Windows).

Exemple d'utilisation avec cron (tous les jours a minuit) :
    0 0 * * * cd /chemin/vers/pipeline_data_engineering && /usr/bin/python3 scheduler.py

Exemple d'utilisation en tant que script Python direct :
    python scheduler.py
"""

import schedule
import time
import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Execute le pipeline complet"""
    logger.info("=" * 60)
    logger.info(f"DEMARRAGE DU PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        result = subprocess.run(
            [sys.executable, 'src/pipeline.py', '--config', 'config.yaml'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        if result.returncode == 0:
            logger.info("PIPELINE TERMINE AVEC SUCCES")
        else:
            logger.error(f"ECHEC DU PIPELINE (code {result.returncode})")
            logger.error(result.stderr)

        logger.info(result.stdout)

    except Exception as e:
        logger.error(f"ERREUR LORS DE L'EXECUTION: {e}", exc_info=True)


def main():
    """Point d'entrée principal du scheduler"""
    logger.info("Scheduler demarre")

    # Planifier l'execution toutes les 24 heures
    schedule.every(24).hours.do(run_pipeline)

    # Planifier une execution de test au demarrage (optionnel)
    # run_pipeline()

    logger.info("Pipeline planifie toutes les 24 heures")

    # Boucle principale
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifier toutes les minutes


if __name__ == '__main__':
    main()
