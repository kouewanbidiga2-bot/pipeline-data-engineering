"""
Chargeur de données vers la base de données

Ce module gère le chargement des données dans le data warehouse.
"""

import logging
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Chargeur de données vers PostgreSQL.
    
    Attributes:
        config (dict): Configuration de la base de données
        engine (Engine): Moteur SQLAlchemy
    """
    
    def __init__(self, config: dict):
        """
        Initialise le chargeur.
        
        Args:
            config: Configuration de la base de données
                - host: Hôte
                - port: Port
                - name: Nom de la base
                - user: Utilisateur
                - password: Mot de passe
        """
        self.config = config
        self.engine: Optional[Engine] = None
    
    def connect(self) -> bool:
        """
        Établit la connexion à la base de données.
        
        Returns:
            bool: True si la connexion a réussi
        """
        try:
            connection_string = (
                f"postgresql://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}"
                f"/{self.config['name']}"
            )
            
            self.engine = create_engine(connection_string)
            
            # Tester la connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Connexion établie à {self.config['host']}:{self.config['port']}/{self.config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur de connexion à la base de données: {e}")
            return False
    
    def close(self):
        """Ferme la connexion à la base de données."""
        if self.engine:
            self.engine.dispose()
            logger.info("Connexion à la base de données fermée")
    
    def load_table(self, table_name: str, data: pd.DataFrame, if_exists: str = 'replace') -> bool:
        """
        Charge un DataFrame dans une table.
        
        Args:
            table_name: Nom de la table
            data: DataFrame à charger
            if_exists: Comportement si la table existe ('replace', 'append', 'fail')
            
        Returns:
            bool: True si le chargement a réussi
        """
        if not self.engine:
            logger.error("Pas de connexion à la base de données")
            return False
        
        try:
            data.to_sql(
                table_name,
                self.engine,
                if_exists=if_exists,
                index=False,
                method='multi',
                chunksize=1000
            )
            
            logger.info(f"Table '{table_name}' chargée: {len(data)} lignes")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de '{table_name}': {e}")
            return False
    
    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """
        Exécute une requête SQL.
        
        Args:
            query: Requête SQL
            
        Returns:
            pd.DataFrame: Résultats de la requête ou None
        """
        if not self.engine:
            logger.error("Pas de connexion à la base de données")
            return None
        
        try:
            with self.engine.connect() as conn:
                result = pd.read_sql(text(query), conn)
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête: {e}")
            return None
    
    def get_table_names(self) -> list:
        """
        Retourne la liste des tables de la base de données.
        
        Returns:
            list: Noms des tables
        """
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                ))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tables: {e}")
            return []
    
    def create_indexes(self, table_name: str, columns: list):
        """
        Crée des index sur une table.
        
        Args:
            table_name: Nom de la table
            columns: Colonnes à indexer
        """
        if not self.engine:
            return
        
        for col in columns:
            index_name = f"idx_{table_name}_{col}"
            try:
                with self.engine.connect() as conn:
                    conn.execute(text(
                        f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({col})"
                    ))
                    conn.commit()
                logger.info(f"Index '{index_name}' créé sur {table_name}({col})")
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'index: {e}")
