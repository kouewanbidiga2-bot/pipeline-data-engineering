"""
Extracteur de données CSV

Ce module gère l'extraction de données depuis des fichiers CSV.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class CSVExtractor:
    """
    Extracteur de données depuis des fichiers CSV.
    
    Attributes:
        source_path (str): Chemin vers le dossier contenant les fichiers CSV
        encoding (str): Encodage des fichiers CSV
        delimiter (str): Délimiteur des fichiers CSV
    """
    
    def __init__(self, source_path: str, encoding: str = 'utf-8', delimiter: str = ','):
        """
        Initialise l'extracteur CSV.
        
        Args:
            source_path: Chemin vers le dossier source
            encoding: Encodage des fichiers (défaut: utf-8)
            delimiter: Délimiteur (défaut: virgule)
        """
        self.source_path = Path(source_path)
        self.encoding = encoding
        self.delimiter = delimiter
        
        if not self.source_path.exists():
            logger.warning(f"Le dossier {source_path} n'existe pas, création...")
            self.source_path.mkdir(parents=True, exist_ok=True)
    
    def extract_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Extrait un fichier CSV unique.
        
        Args:
            file_path: Chemin vers le fichier CSV
            
        Returns:
            pd.DataFrame: Données extraites ou None en cas d'erreur
        """
        try:
            full_path = self.source_path / file_path
            df = pd.read_csv(
                full_path,
                encoding=self.encoding,
                delimiter=self.delimiter
            )
            logger.info(f"Fichier {file_path} extrait: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
        except FileNotFoundError:
            logger.error(f"Fichier non trouvé: {file_path}")
            return None
        except pd.errors.EmptyDataError:
            logger.warning(f"Fichier vide: {file_path}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de {file_path}: {e}")
            return None
    
    def extract_all(self) -> Dict[str, pd.DataFrame]:
        """
        Extrait tous les fichiers CSV du dossier source.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionnaire des données extraites par fichier
        """
        results = {}
        
        if not self.source_path.exists():
            logger.warning(f"Le dossier {self.source_path} n'existe pas")
            return results
        
        csv_files = list(self.source_path.glob("*.csv"))
        logger.info(f"{len(csv_files)} fichiers CSV trouvés dans {self.source_path}")
        
        for csv_file in csv_files:
            df = self.extract_file(csv_file.name)
            if df is not None:
                results[csv_file.stem] = df
        
        return results
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Retourne les informations sur un fichier CSV.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            dict: Informations sur le fichier ou None
        """
        try:
            full_path = self.source_path / file_path
            df = pd.read_csv(full_path, nrows=0)
            
            return {
                'name': file_path,
                'columns': list(df.columns),
                'column_count': len(df.columns),
                'size_bytes': full_path.stat().st_size
            }
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des informations de {file_path}: {e}")
            return None
