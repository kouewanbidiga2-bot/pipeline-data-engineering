"""
Tests unitaires du pipeline Data Engineering
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.extract.csv_extractor import CSVExtractor
from src.transform.cleaner import DataCleaner
from src.transform.aggregator import DataAggregator
from src.validate.quality_checker import QualityChecker


class TestCSVExtractor:
    """Tests pour l'extracteur CSV."""
    
    def test_extract_file_not_found(self, tmp_path):
        """Test de l'extraction d'un fichier inexistant."""
        extractor = CSVExtractor(str(tmp_path))
        result = extractor.extract_file("nonexistent.csv")
        assert result is None
    
    def test_extract_all_empty_directory(self, tmp_path):
        """Test de l'extraction dans un dossier vide."""
        extractor = CSVExtractor(str(tmp_path))
        result = extractor.extract_all()
        assert result == {}
    
    def test_extract_all_with_files(self, tmp_path):
        """Test de l'extraction avec fichiers CSV."""
        # Créer un fichier CSV de test
        df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['Paris', 'London', 'New York']
        })
        df.to_csv(tmp_path / "test.csv", index=False)
        
        extractor = CSVExtractor(str(tmp_path))
        result = extractor.extract_all()
        
        assert "test" in result
        assert len(result["test"]) == 3
        assert list(result["test"].columns) == ['name', 'age', 'city']


class TestDataCleaner:
    """Tests pour le nettoyeur de données."""
    
    def test_remove_duplicates(self):
        """Test de la suppression des doublons."""
        df = pd.DataFrame({
            'A': [1, 2, 2, 3],
            'B': ['a', 'b', 'b', 'c']
        })
        
        cleaner = DataCleaner()
        result = cleaner.remove_duplicates(df)
        
        assert len(result) == 3
    
    def test_handle_missing_values_numeric(self):
        """Test de la gestion des valeurs manquantes numériques."""
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4],
            'B': [10, 20, 30, 40]
        })
        
        cleaner = DataCleaner()
        result = cleaner.handle_missing_values(df, strategy='auto')
        
        assert result['A'].isnull().sum() == 0
    
    def test_clean_strings(self):
        """Test du nettoyage des chaînes."""
        df = pd.DataFrame({
            'name': ['  Alice  ', 'BOB', '  charlie  ']
        })
        
        cleaner = DataCleaner()
        result = cleaner.clean_strings(df)
        
        assert result['name'].iloc[0] == 'Alice'
        assert result['name'].iloc[1] == 'BOB'
    
    def test_full_cleaning_pipeline(self):
        """Test du pipeline de nettoyage complet."""
        df = pd.DataFrame({
            'A': [1, 2, 2, np.nan],
            'B': ['  x  ', 'y', 'y', 'z'],
            'C': [np.nan, np.nan, np.nan, np.nan]
        })
        
        cleaner = DataCleaner()
        result = cleaner.clean(df)
        
        # Les doublons doivent être supprimés
        assert len(result) <= 3
        # La colonne C (100% manquante) doit être supprimée
        assert 'C' not in result.columns


class TestDataAggregator:
    """Tests pour l'agrégateur de données."""
    
    def test_add_rolling_features(self):
        """Test de l'ajout de features de moyenne mobile."""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5]
        })
        
        aggregator = DataAggregator()
        result = aggregator.add_rolling_features(df, 'value', windows=[2])
        
        assert 'value_rolling_2' in result.columns
    
    def test_add_lag_features(self):
        """Test de l'ajout de features de décalage."""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5]
        })
        
        aggregator = DataAggregator()
        result = aggregator.add_lag_features(df, 'value', lags=[1])
        
        assert 'value_lag_1' in result.columns
        assert pd.isna(result['value_lag_1'].iloc[0])
    
    def test_add_date_features(self):
        """Test de l'ajout de features de date."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        aggregator = DataAggregator()
        result = aggregator.add_date_features(df, 'date')
        
        assert 'date_year' in result.columns
        assert 'date_month' in result.columns
        assert 'date_day' in result.columns


class TestQualityChecker:
    """Tests pour le vérificateur de qualité."""
    
    def test_check_completeness(self):
        """Test de vérification de la complétude."""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        
        config = {'completeness_threshold': 0.95}
        checker = QualityChecker(config)
        result = checker.check_completeness(df)
        
        assert result['passed'] is True
        assert result['value'] == '100.00%'
    
    def test_check_completeness_with_missing(self):
        """Test de complétude avec valeurs manquantes."""
        df = pd.DataFrame({
            'A': [1, 2, np.nan],
            'B': [4, 5, 6]
        })
        
        config = {'completeness_threshold': 0.95}
        checker = QualityChecker(config)
        result = checker.check_completeness(df)
        
        assert result['passed'] is False
    
    def test_check_uniqueness(self):
        """Test de vérification de l'unicité."""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['a', 'b', 'c']
        })
        
        config = {'uniqueness_threshold': 1.0}
        checker = QualityChecker(config)
        result = checker.check_uniqueness(df)
        
        assert result['passed'] is True
    
    def test_check_uniqueness_with_duplicates(self):
        """Test d'unicité avec doublons."""
        df = pd.DataFrame({
            'A': [1, 2, 2],
            'B': ['a', 'b', 'b']
        })
        
        config = {'uniqueness_threshold': 1.0}
        checker = QualityChecker(config)
        result = checker.check_uniqueness(df)
        
        assert result['passed'] is False
    
    def test_full_quality_check(self):
        """Test de vérification qualité complète."""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['a', 'b', 'c']
        })
        
        config = {
            'completeness_threshold': 0.95,
            'uniqueness_threshold': 1.0,
            'validity_threshold': 0.98
        }
        checker = QualityChecker(config)
        result = checker.check(df)
        
        assert 'completeness' in result
        assert 'uniqueness' in result
        assert 'validity' in result
        assert 'consistency' in result
        assert 'freshness' in result


class TestIntegration:
    """Tests d'intégration."""
    
    def test_full_pipeline(self, tmp_path):
        """Test du pipeline complet."""
        # Créer des données de test
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=100),
            'value': np.random.randn(100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        })
        df.to_csv(tmp_path / "test_data.csv", index=False)
        
        # Extraction
        extractor = CSVExtractor(str(tmp_path))
        raw_data = extractor.extract_all()
        
        assert "test_data" in raw_data
        
        # Nettoyage
        cleaner = DataCleaner()
        cleaned = cleaner.clean(raw_data["test_data"])
        
        assert len(cleaned) > 0
        
        # Validation
        config = {
            'completeness_threshold': 0.95,
            'uniqueness_threshold': 1.0,
            'validity_threshold': 0.98
        }
        checker = QualityChecker(config)
        quality = checker.check(cleaned)
        
        assert 'completeness' in quality
        assert 'uniqueness' in quality


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
