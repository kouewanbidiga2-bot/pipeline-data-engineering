"""
Vérificateur de qualité des données

Ce module gère la validation de la qualité des données.
"""

import logging
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class QualityChecker:
    """
    Vérificateur de qualité des données avec métriques configurables.
    
    Attributes:
        config (dict): Configuration des seuils de qualité
    """
    
    def __init__(self, config: dict):
        """
        Initialise le vérificateur.
        
        Args:
            config: Configuration des seuils
                - completeness_threshold: Seuil de complétude (0-1)
                - uniqueness_threshold: Seuil d'unicité (0-1)
                - validity_threshold: Seuil de validité (0-1)
        """
        self.config = config
    
    def check(self, data: pd.DataFrame) -> Dict[str, dict]:
        """
        Vérifie la qualité d'un DataFrame.
        
        Args:
            data: DataFrame à vérifier
            
        Returns:
            Dict[str, dict]: Résultats des vérifications par métrique
        """
        results = {
            'completeness': self.check_completeness(data),
            'uniqueness': self.check_uniqueness(data),
            'validity': self.check_validity(data),
            'consistency': self.check_consistency(data),
            'freshness': self.check_freshness(data)
        }
        
        return results
    
    def check_completeness(self, data: pd.DataFrame) -> dict:
        """
        Vérifie la complétude des données (valeurs manquantes).
        
        Args:
            data: DataFrame à vérifier
            
        Returns:
            dict: Résultat de la vérification
        """
        total_cells = data.size
        missing_cells = data.isnull().sum().sum()
        completeness = 1 - (missing_cells / total_cells) if total_cells > 0 else 0
        
        threshold = self.config.get('completeness_threshold', 0.95)
        passed = completeness >= threshold
        
        return {
            'value': f"{completeness:.2%}",
            'threshold': f"{threshold:.0%}",
            'passed': passed,
            'missing_cells': int(missing_cells),
            'total_cells': int(total_cells)
        }
    
    def check_uniqueness(self, data: pd.DataFrame) -> dict:
        """
        Vérifie l'unicité des lignes.
        
        Args:
            data: DataFrame à vérifier
            
        Returns:
            dict: Résultat de la vérification
        """
        total_rows = len(data)
        duplicate_rows = data.duplicated().sum()
        uniqueness = 1 - (duplicate_rows / total_rows) if total_rows > 0 else 0
        
        threshold = self.config.get('uniqueness_threshold', 1.0)
        passed = uniqueness >= threshold
        
        return {
            'value': f"{uniqueness:.2%}",
            'threshold': f"{threshold:.0%}",
            'passed': passed,
            'duplicate_rows': int(duplicate_rows),
            'total_rows': int(total_rows)
        }
    
    def check_validity(self, data: pd.DataFrame) -> dict:
        """
        Vérifie la validité des données (types, formats).
        
        Args:
            data: DataFrame à vérifier
            
        Returns:
            dict: Résultat de la vérification
        """
        # Vérification basique : pas de valeurs infinies ou NaN dans les colonnes numériques
        numeric_cols = data.select_dtypes(include=['number']).columns
        
        invalid_count = 0
        for col in numeric_cols:
            invalid_count += data[col].isin([float('inf'), float('-inf')]).sum()
        
        total_numeric = len(numeric_cols) * len(data) if len(numeric_cols) > 0 else 1
        validity = 1 - (invalid_count / total_numeric) if total_numeric > 0 else 1
        
        threshold = self.config.get('validity_threshold', 0.98)
        passed = validity >= threshold
        
        return {
            'value': f"{validity:.2%}",
            'threshold': f"{threshold:.0%}",
            'passed': passed,
            'invalid_values': int(invalid_count)
        }
    
    def check_consistency(self, data: pd.DataFrame) -> dict:
        """
        Vérifie la cohérence des données.
        
        Args:
            data: DataFrame à vérifier
            
        Returns:
            dict: Résultat de la vérification
        """
        # Vérification basique : cohérence des types
        consistency_issues = 0
        
        for col in data.columns:
            # Vérifier que le type est cohérent
            unique_types = data[col].dropna().apply(type).nunique()
            if unique_types > 1:
                consistency_issues += 1
        
        total_cols = len(data.columns)
        consistency = 1 - (consistency_issues / total_cols) if total_cols > 0 else 1
        
        return {
            'value': f"{consistency:.2%}",
            'threshold": "95%",
            'passed': consistency >= 0.95,
            'issues': consistency_issues
        }
    
    def check_freshness(self, data: pd.DataFrame) -> dict:
        """
        Vérifie la fraîcheur des données.
        
        Args:
            data: DataFrame à vérifier
            
        Returns:
            dict: Résultat de la vérification
        """
        # Chercher une colonne de date
        date_cols = [col for col in data.columns if 'date' in col.lower() or 'time' in col.lower()]
        
        if not date_cols:
            return {
                'value': 'N/A',
                'threshold': 'N/A',
                'passed': True,
                'note': 'Aucune colonne de date trouvée'
            }
        
        # Utiliser la première colonne de date trouvée
        date_col = date_cols[0]
        
        try:
            dates = pd.to_datetime(data[date_col], errors='coerce')
            max_date = dates.max()
            
            if pd.isna(max_date):
                return {
                    'value': 'N/A',
                    'threshold': 'N/A',
                    'passed': False,
                    'note': 'Impossible de parser les dates'
                }
            
            # Vérifier si les données sont récentes (moins de 30 jours)
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=30)
            is_fresh = max_date >= cutoff_date
            
            return {
                'value': max_date.strftime('%Y-%m-%d'),
                'threshold': cutoff_date.strftime('%Y-%m-%d'),
                'passed': is_fresh,
                'note': f"Dernière date: {max_date.strftime('%Y-%m-%d')}"
            }
        except Exception as e:
            return {
                'value': 'N/A',
                'threshold': 'N/A',
                'passed': False,
                'note': f'Erreur: {str(e)}'
            }
    
    def generate_report(self, results: Dict[str, dict]) -> str:
        """
        Génère un rapport de qualité formaté.
        
        Args:
            results: Résultats des vérifications
            
        Returns:
            str: Rapport formaté
        """
        report = []
        report.append("=" * 60)
        report.append("RAPPORT QUALITÉ DES DONNÉES")
        report.append("=" * 60)
        
        all_passed = True
        
        for metric, result in results.items():
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            report.append(f"\n{metric.upper()}:")
            report.append(f"  Statut: {status}")
            report.append(f"  Valeur: {result['value']}")
            report.append(f"  Seuil: {result['threshold']}")
            
            if not result['passed']:
                all_passed = False
        
        report.append("\n" + "=" * 60)
        report.append(f"RÉSULTAT GLOBAL: {'✓ TOUS LES TESTS PASSENT' if all_passed else '✗ CERTAINS TESTS ÉCHOUENT'}")
        report.append("=" * 60)
        
        return "\n".join(report)
