"""
Tests d'integration — Pipeline Data Engineering

Ces tests necessitent une base de PostgreSQL fonctionnelle.
Lancer avec : pytest tests/test_integration.py -v
"""

import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# Configuration de la base de donnees (adapter selon l'environnement)
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'name': os.getenv('DB_NAME', 'data_warehouse'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
}

def get_connection_string():
    return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['name']}"


@pytest.fixture(scope='module')
def db_engine():
    """Fixture pour la connexion à la base de données"""
    engine = create_engine(get_connection_string())
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def setup_test_table(db_engine):
    """Nettoie la table de test avant chaque test"""
    with db_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS test_employees CASCADE"))
        conn.execute(text("""
            CREATE TABLE test_employees (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                department VARCHAR(50),
                salary NUMERIC(10,2),
                hire_date DATE DEFAULT CURRENT_DATE
            )
        """))
        conn.commit()
    yield
    with db_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS test_employees CASCADE"))
        conn.commit()


def test_insert_and_query(db_engine):
    """Test d'insertion et de requête simple"""
    with db_engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO test_employees (name, department, salary) VALUES "
            "('Alice', 'Engineering', 75000),"
            "('Bob', 'Marketing', 65000),"
            "('Charlie', 'Engineering', 80000)"
        ))
        conn.commit()

        result = conn.execute(text("SELECT COUNT(*) FROM test_employees"))
        count = result.scalar()
        assert count == 3, f"Attendu 3, obtenu {count}"


def test_aggregate_query(db_engine):
    """Test de requête d'agrégation"""
    with db_engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO test_employees (name, department, salary) VALUES "
            "('Alice', 'Engineering', 75000),"
            "('Bob', 'Marketing', 65000),"
            "('Charlie', 'Engineering', 80000),"
            "('Diana', 'Engineering', 90000)"
        ))
        conn.commit()

        result = conn.execute(text(
            "SELECT department, AVG(salary) as avg_salary, COUNT(*) as count "
            "FROM test_employees GROUP BY department ORDER BY department"
        ))
        rows = result.fetchall()

        eng_row = [r for r in rows if r[0] == 'Engineering'][0]
        assert eng_row[2] == 3  # 3 employes en Engineering
        assert float(eng_row[1]) == 81666.67  # Moyenne des salaires


def test_data_quality_completeness(db_engine):
    """Test de qualité des données - complétude"""
    with db_engine.connect() as conn:
        # Insertion avec valeurs manquantes
        conn.execute(text(
            "INSERT INTO test_employees (name, department, salary) VALUES "
            "('Alice', 'Engineering', 75000),"
            "('Bob', NULL, 65000),"
            "('Charlie', 'Engineering', NULL)"
        ))
        conn.commit()

        result = conn.execute(text(
            "SELECT COUNT(*) FROM test_employees "
            "WHERE department IS NULL OR salary IS NULL"
        ))
        missing = result.scalar()
        assert missing == 2, f"Attendu 2 valeurs manquantes, obtenu {missing}"


def test_data_quality_uniqueness(db_engine):
    """Test de qualité des données - unicité"""
    with db_engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO test_employees (id, name, department, salary) VALUES "
            "(1, 'Alice', 'Engineering', 75000),"
            "(2, 'Bob', 'Marketing', 65000)"
        ))
        conn.commit()

        # Test de contrainte d'unicité (PRIMARY KEY)
        with pytest.raises(Exception):
            conn.execute(text(
                "INSERT INTO test_employees (id, name, department, salary) "
                "VALUES (1, 'Charlie', 'Engineering', 80000)"
            ))
            conn.commit()


def test_data_freshness(db_engine):
    """Test de fraîcheur des données"""
    with db_engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO test_employees (name, department, salary, hire_date) VALUES "
            "('Alice', 'Engineering', 75000, '2024-01-15'),"
            "('Bob', 'Marketing', 65000, '2024-01-16'),"
            "('Charlie', 'Engineering', 80000, '2024-01-17)"
        ))
        conn.commit()

        result = conn.execute(text(
            "SELECT MAX(hire_date) FROM test_employees"
        ))
        max_date = result.scalar()
        assert max_date is not None
        # Verifier que les donnees sont recentes (moins de 1 an)
        assert (datetime.now().date() - max_date).days < 365


def test_pipeline_extract_transform(db_engine):
    """Test du pipeline ETL complet avec données réelles"""
    from src.extract.csv_extractor import CSVExtractor
    from src.transform.cleaner import DataCleaner

    # Extraction
    extractor = CSVExtractor('data/raw')
    raw_data = extractor.extract_all()

    assert len(raw_data) > 0, "Aucun fichier CSV trouvé"
    assert 'exemple_donnees' in raw_data or 'aqua_optim_donnees' in raw_data

    # Nettoyage
    cleaner = DataCleaner()
    for name, df in raw_data.items():
        cleaned = cleaner.clean(df)
        assert len(cleaned) > 0, f"Données vides après nettoyage pour {name}"
        assert cleaned.isnull().sum().sum() == 0, f"Valeurs manquantes après nettoyage pour {name}"

    # Chargement (simulé)
    for name, df in raw_data.items():
        with db_engine.connect() as conn:
            df.to_sql(f'staging_{name}', conn, if_exists='replace', index=False)
            result = conn.execute(text(f"SELECT COUNT(*) FROM staging_{name}"))
            count = result.scalar()
            assert count == len(df), f"Nombre de lignes incorrect pour {name}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
