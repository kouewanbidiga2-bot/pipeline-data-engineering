"""
Nettoyeur de données

Ce module gère le nettoyage et la préparation des données.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Nettoyeur de données avec opérations de nettoyage courantes.
    """
    
    def __init__(self):
        """Initialise le nettoyeur."""
        self.cleaning_stats = {}
    
    def clean(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Applique toutes les opérations de nettoyage.
        
        Args:
            data: DataFrame à nettoyer
            
        Returns:
            pd.DataFrame: DataFrame nettoyé
        """
        logger.info(f"Début du nettoyage: {len(data)} lignes, {len(data.columns)} colonnes")
        
        initial_rows = len(data)
        initial_cols = len(data.columns)
        
        # 1. Suppression des doublons
        data = self.remove_duplicates(data)
        
        # 2. Gestion des valeurs manquantes
        data = self.handle_missing_values(data)
        
        # 3. Normalisation des types
        data = self.normalize_types(data)
        
        # 4. Suppression des colonnes vides
        data = self.remove_empty_columns(data)
        
        # 5. Nettoyage des chaînes de caractères
        data = self.clean_strings(data)
        
        final_rows = len(data)
        final_cols = len(data.columns)
        
        self.cleaning_stats = {
            'initial_rows': initial_rows,
            'final_rows': final_rows,
            'rows_removed': initial_rows - final_rows,
            'initial_columns': initial_cols,
            'final_columns': final_cols,
            'columns_removed': initial_cols - final_cols
        }
        
        logger.info(f"Nettoyage terminé: {final_rows} lignes, {final_cols} colonnes")
        logger.info(f"  -> {self.cleaning_stats['rows_removed']} lignes supprimées")
        logger.info(f"  -> {self.cleaning_stats['columns_removed']} colonnes supprimées")
        
        return data
    
    def remove_duplicates(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les lignes dupliquées.
        
        Args:
            data: DataFrame à nettoyer
            
        Returns:
            pd.DataFrame: DataFrame sans doublons
        """
        initial_count = len(data)
        data = data.drop_duplicates()
        removed = initial_count - len(data)
        
        if removed > 0:
            logger.info(f"  {removed} doublons supprimés")
        
        return data
    
    def handle_missing_values(self, data: pd.DataFrame, strategy: str = 'auto') -> pd.DataFrame:
        """
        Gère les valeurs manquantes selon la stratégie choisie.
        
        Args:
            data: DataFrame à nettoyer
            strategy: Stratégie ('auto', 'drop', 'fill_mean', 'fill_median', 'fill_mode')
            
        Returns:
            pd.DataFrame: DataFrame avec valeurs manquantes gérées
        """
        missing_before = data.isnull().sum().sum()
        
        if missing_before == 0:
            logger.info("  Aucune valeur manquante")
            return data
        
        logger.info(f"  {missing_before} valeurs manquantes détectées")
        
        if strategy == 'auto':
            # Stratégie automatique selon le type de colonne
            for col in data.columns:
                missing_pct = data[col].isnull().sum() / len(data)
                
                if missing_pct > 0.5:
                    # Plus de 50% manquant -> supprimer la colonne
                    logger.info(f"    Colonne '{col}' supprimée ({missing_pct:.1%} manquant)")
                    data = data.drop(columns=[col])
                elif data[col].dtype in ['int64', 'float64']:
                    # Numérique -> remplir par la médiane
                    median_val = data[col].median()
                    data[col] = data[col].fillna(median_val)
                    logger.info(f"    Colonne '{col}' remplie par la médiane ({median_val})")
                else:
                    # Catégoriel -> remplir par le mode
                    mode_val = data[col].mode()
                    if len(mode_val) > 0:
                        data[col] = data[col].fillna(mode_val[0])
                        logger.info(f"    Colonne '{col}' remplie par le mode ({mode_val[0]})")
        
        elif strategy == 'drop':
            data = data.dropna()
        
        return data
    
    def normalize_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalise et convertit les types de données.
        
        Args:
            data: DataFrame à normaliser
            
        Returns:
            pd.DataFrame: DataFrame avec types normalisés
        """
        for col in data.columns:
            # Tentative de conversion en numérique
            if data[col].dtype == 'object':
                try:
                    data[col] = pd.to_numeric(data[col])
                    logger.info(f"    Colonne '{col}' convertie en numérique")
                except (ValueError, TypeError):
                    pass
            
            # Tentative de conversion en datetime
            if data[col].dtype == 'object' and 'date' in col.lower():
                try:
                    data[col] = pd.to_datetime(data[col])
                    logger.info(f"    Colonne '{col}' convertie en datetime")
                except (ValueError, TypeError):
                    pass
        
        return data
    
    def remove_empty_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les colonnes entièrement vides.
        
        Args:
            data: DataFrame à nettoyer
            
        Returns:
            pd.DataFrame: DataFrame sans colonnes vides
        """
        empty_cols = data.columns[data.isnull().all()].tolist()
        
        if empty_cols:
            data = data.drop(columns=empty_cols)
            logger.info(f"  Colonnes vides supprimées: {empty_cols}")
        
        return data
    
    def clean_strings(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les chaînes de caractères (espaces, casse).
        
        Args:
            data: DataFrame à nettoyer
            
        Returns:
            pd.DataFrame: DataFrame avec chaînes nettoyées
        """
        for col in data.select_dtypes(include=['object']).columns:
            # Suppression des espaces en début/fin
            data[col] = data[col].str.strip()
            
            # Normalisation des espaces multiples
            data[col] = data[col].str.replace(r'\s+', ' ', regex=True)
        
        return data
    
    def get_stats(self) -> dict:
        """
        Retourne les statistiques de nettoyage.
        
        Returns:
            dict: Statistiques de nettoyage
        """
        return self.cleaning_stats.copy()
