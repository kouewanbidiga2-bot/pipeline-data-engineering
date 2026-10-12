"""
Pipeline Data Engineering — Orchestrateur principal

Ce module orchestre l'ensemble du pipeline ETL :
1. Extract : Récupération des données depuis les sources
2. Transform : Nettoyage, agrégation et feature engineering
3. Load : Chargement dans le data warehouse
4. Validate : Contrôle qualité des données
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from extract.csv_extractor import CSVExtractor
from extract.api_extractor import APIExtractor
from transform.cleaner import DataCleaner
from transform.aggregator import DataAggregator
from load.db_loader import DatabaseLoader
from validate.quality_checker import QualityChecker

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Pipeline de données complet avec orchestration ETL.
    
    Attributes:
        config (dict): Configuration du pipeline
        extractor: Extracteur de données
        cleaner: Nettoyeur de données
        aggregator: Agrégateur de données
        loader: Chargeur de données
        quality_checker: Vérificateur de qualité
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialise le pipeline avec la configuration.
        
        Args:
            config_path: Chemin vers le fichier de configuration YAML
        """
        self.config = self._load_config(config_path)
        self.extractor = None
        self.cleaner = DataCleaner()
        self.aggregator = DataAggregator()
        self.loader = DatabaseLoader(self.config.get('database', {}))
        self.quality_checker = QualityChecker(self.config.get('quality', {}))
        
        logger.info("Pipeline initialisé avec succès")
    
    def _load_config(self, config_path: str) -> dict:
        """
        Charge la configuration depuis un fichier YAML.
        
        Args:
            config_path: Chemin vers le fichier de configuration
            
        Returns:
            dict: Configuration chargée
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration chargée depuis {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Fichier de configuration {config_path} non trouvé, utilisation des valeurs par défaut")
            return self._default_config()
        except yaml.YAMLError as e:
            logger.error(f"Erreur de parsing YAML: {e}")
            raise
    
    def _default_config(self) -> dict:
        """Retourne la configuration par défaut."""
        return {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'data_warehouse',
                'user': 'postgres',
                'password': ''
            },
            'quality': {
                'completeness_threshold': 0.95,
                'uniqueness_threshold': 1.0,
                'validity_threshold': 0.98
            },
            'sources': {
                'csv': {'enabled': True, 'path': 'data/raw/'},
                'api': {'enabled': False, 'url': ''},
                'database': {'enabled': False, 'connection_string': ''}
            }
        }
    
    def extract(self) -> dict:
        """
        Étape 1 : Extraction des données depuis les sources configurées.
        
        Returns:
            dict: Données brutes extraites par source
        """
        logger.info("=== ÉTAPE 1: EXTRACTION ===")
        raw_data = {}
        
        # Extraction CSV
        if self.config.get('sources', {}).get('csv', {}).get('enabled', False):
            logger.info("Extraction des données CSV...")
            csv_extractor = CSVExtractor(self.config['sources']['csv']['path'])
            raw_data['csv'] = csv_extractor.extract_all()
            logger.info(f"  -> {len(raw_data['csv'])} fichiers CSV extraits")
        
        # Extraction API
        if self.config.get('sources', {}).get('api', {}).get('enabled', False):
            logger.info("Extraction des données API...")
            api_extractor = APIExtractor(self.config['sources']['api']['url'])
            raw_data['api'] = api_extractor.extract()
            logger.info(f"  -> Données API extraites")
        
        # Extraction Base de données
        if self.config.get('sources', {}).get('database', {}).get('enabled', False):
            logger.info("Extraction des données base de données...")
            # TODO: Implémenter l'extraction depuis la base de données
            pass
        
        logger.info(f"Extraction terminée: {len(raw_data)} sources traitées")
        return raw_data
    
    def transform(self, raw_data: dict) -> dict:
        """
        Étape 2 : Transformation des données (nettoyage, agrégation, feature engineering).
        
        Args:
            raw_data: Données brutes extraites
            
        Returns:
            dict: Données transformées
        """
        logger.info("=== ÉTAPE 2: TRANSFORMATION ===")
        transformed_data = {}
        
        for source_name, data in raw_data.items():
            logger.info(f"Transformation des données {source_name}...")
            
            # Nettoyage
            cleaned = self.cleaner.clean(data)
            
            # Agrégation
            aggregated = self.aggregator.aggregate(cleaned)
            
            # Feature engineering
            # TODO: Ajouter le feature engineering spécifique au domaine
            
            transformed_data[source_name] = aggregated
            logger.info(f"  -> {len(aggregated)} enregistrements transformés")
        
        logger.info("Transformation terminée")
        return transformed_data
    
    def load(self, transformed_data: dict) -> bool:
        """
        Étape 3 : Chargement des données dans le data warehouse.
        
        Args:
            transformed_data: Données transformées
            
        Returns:
            bool: True si le chargement a réussi
        """
        logger.info("=== ÉTAPE 3: CHARGEMENT ===")
        
        try:
            self.loader.connect()
            
            for table_name, data in transformed_data.items():
                logger.info(f"Chargement de {table_name}...")
                self.loader.load_table(table_name, data)
                logger.info(f"  -> {len(data)} enregistrements chargés")
            
            self.loader.close()
            logger.info("Chargement terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            return False
    
    def validate(self, data: dict) -> dict:
        """
        Étape 4 : Validation de la qualité des données.
        
        Args:
            data: Données à valider
            
        Returns:
            dict: Résultats de la validation
        """
        logger.info("=== ÉTAPE 4: VALIDATION QUALITÉ ===")
        results = {}
        
        for table_name, table_data in data.items():
            logger.info(f"Validation de {table_name}...")
            quality_report = self.quality_checker.check(table_data)
            results[table_name] = quality_report
            
            # Log des résultats
            for metric, value in quality_report.items():
                status = "✓" if value.get('passed', False) else "✗"
                logger.info(f"  {status} {metric}: {value.get('value', 'N/A')}")
        
        logger.info("Validation terminée")
        return results
    
    def run(self) -> bool:
        """
        Exécute le pipeline complet.
        
        Returns:
            bool: True si le pipeline a réussi
        """
        logger.info("=" * 60)
        logger.info("DÉMARRAGE DU PIPELINE DATA ENGINEERING")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Étape 1: Extraction
            raw_data = self.extract()
            
            # Étape 2: Transformation
            transformed_data = self.transform(raw_data)
            
            # Étape 3: Chargement
            load_success = self.load(transformed_data)
            
            if not load_success:
                logger.error("Le pipeline a échoué au chargement")
                return False
            
            # Étape 4: Validation
            quality_results = self.validate(transformed_data)
            
            # Résumé
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info("PIPELINE TERMINÉ AVEC SUCCÈS")
            logger.info(f"Durée totale: {duration:.2f} secondes")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Le pipeline a échoué: {e}", exc_info=True)
            return False


def main():
    """Point d'entrée principal."""
    # Créer les dossiers nécessaires
    Path("logs").mkdir(exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/warehouse").mkdir(parents=True, exist_ok=True)
    
    # Initialiser et exécuter le pipeline
    pipeline = DataPipeline("config.yaml")
    success = pipeline.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
