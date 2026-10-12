"""
Agrégateur de données

Ce module gère l'agrégation et le feature engineering des données.
"""

import logging
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Agrégateur de données avec opérations d'agrégation courantes.
    """
    
    def __init__(self):
        """Initialise l'agrégateur."""
        self.aggregation_stats = {}
    
    def aggregate(self, data: pd.DataFrame, group_by: Optional[List[str]] = None,
                  aggregations: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Agrège les données selon les colonnes et fonctions spécifiées.
        
        Args:
            data: DataFrame à agréger
            group_by: Colonnes de regroupement
            aggregations: Dictionnaire {colonne: fonction}
            
        Returns:
            pd.DataFrame: DataFrame agrégé
        """
        if group_by is None or aggregations is None:
            logger.info("Pas d'agrégation spécifiée, retour des données telles quelles")
            return data
        
        logger.info(f"Agrégation par {group_by} avec {list(aggregations.keys())} fonctions")
        
        try:
            aggregated = data.groupby(group_by).agg(aggregations).reset_index()
            logger.info(f"  -> {len(aggregated)} groupes créés")
            return aggregated
        except Exception as e:
            logger.error(f"Erreur lors de l'agrégation: {e}")
            return data
    
    def add_rolling_features(self, data: pd.DataFrame, column: str,
                            windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
        """
        Ajoute des features de moyenne mobile.
        
        Args:
            data: DataFrame source
            column: Colonne pour calculer les moyennes mobiles
            windows: Liste des fenêtres de temps
            
        Returns:
            pd.DataFrame: DataFrame avec nouvelles features
        """
        for window in windows:
            col_name = f"{column}_rolling_{window}"
            data[col_name] = data[column].rolling(window=window, min_periods=1).mean()
            logger.info(f"Feature ajoutée: {col_name}")
        
        return data
    
    def add_lag_features(self, data: pd.DataFrame, column: str,
                        lags: List[int] = [1, 7, 14]) -> pd.DataFrame:
        """
        Ajoute des features de décalage temporel (lag).
        
        Args:
            data: DataFrame source
            column: Colonne pour décaler
            lags: Liste des décalages
            
        Returns:
            pd.DataFrame: DataFrame avec nouvelles features
        """
        for lag in lags:
            col_name = f"{column}_lag_{lag}"
            data[col_name] = data[column].shift(lag)
            logger.info(f"Feature ajoutée: {col_name}")
        
        return data
    
    def add_date_features(self, data: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Ajoute des features basées sur la date.
        
        Args:
            data: DataFrame source
            date_column: Colonne de date
            
        Returns:
            pd.DataFrame: DataFrame avec nouvelles features
        """
        try:
            dates = pd.to_datetime(data[date_column])
            
            data[f"{date_column}_year"] = dates.dt.year
            data[f"{date_column}_month"] = dates.dt.month
            data[f"{date_column}_day"] = dates.dt.day
            data[f"{date_column}_dayofweek"] = dates.dt.dayofweek
            data[f"{date_column}_quarter"] = dates.dt.quarter
            
            logger.info(f"Features date ajoutées pour {date_column}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des features date: {e}")
        
        return data
    
    def get_stats(self) -> dict:
        """
        Retourne les statistiques d'agrégation.
        
        Returns:
            dict: Statistiques d'agrégation
        """
        return self.aggregation_stats.copy()
