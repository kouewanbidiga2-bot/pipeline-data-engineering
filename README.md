# Pipeline Data Engineering — Projet Publiable

> **Objectif** : Démontrer mes compétences en Data Engineering avec un pipeline reproductible, testé et documenté.

---

## Aperçu

Ce projet est un pipeline de données complet qui :
1. **Extrait** des données de sources multiples (CSV, API, base de données)
2. **Transforme** les données (nettoyage, agrégation, feature engineering)
3. **Charge** les données dans un data warehouse (PostgreSQL)
4. **Valide** la qualité des données avec des tests automatisés
5. **Documente** le pipeline avec des métriques et des rapports

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Sources       │     │   Pipeline      │     │   Warehouse     │
│                 │     │                 │     │                 │
│  - CSV files    │────▶│  - Extract      │────▶│  - PostgreSQL   │
│  - API REST     │     │  - Transform    │     │  - Tables       │
│  - Database     │     │  - Validate     │     │  - Indexes      │
│                 │     │  - Load         │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Monitoring    │
                        │                 │
                        │  - Logs         │
                        │  - Metrics      │
                        │  - Alerts       │
                        └─────────────────┘
```

---

## Structure du projet

```
pipeline_data_engineering/
├── src/
│   ├── extract/           # Extraction des données
│   │   ├── csv_extractor.py
│   │   ├── api_extractor.py
│   │   └── db_extractor.py
│   ├── transform/         # Transformation des données
│   │   ├── cleaner.py
│   │   ├── aggregator.py
│   │   └── feature_engineer.py
│   ├── load/              # Chargement des données
│   │   ├── db_loader.py
│   │   └── warehouse.py
│   ├── validate/          # Validation qualité
│   │   ├── schema_validator.py
│   │   ├── quality_checker.py
│   │   └── tests/
│   │       ├── test_extract.py
│   │       ├── test_transform.py
│   │       └── test_load.py
│   ├── pipeline.py        # Orchestrateur principal
│   └── config.py          # Configuration
├── data/
│   ├── raw/               # Données brutes
│   ├── processed/         # Données transformées
│   └── warehouse/         # Données chargées
├── notebooks/             # Notebooks d'analyse
├── tests/                 # Tests unitaires et intégration
├── docs/                  # Documentation
├── requirements.txt       # Dépendances
├── Dockerfile             # Containerisation
└── README.md              # Ce fichier
```

---

## Installation

```bash
# Cloner le repository
git clone https://github.com/kouewanbidiga2-bot/pipeline-data-engineering.git
cd pipeline-data-engineering

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations
```

---

## Utilisation

### Lancer le pipeline complet

```bash
python src/pipeline.py --config config.yaml
```

### Lancer les tests

```bash
pytest tests/ -v --cov=src
```

### Lancer avec Docker

```bash
docker build -t data-pipeline .
docker run --env-file .env data-pipeline
```

---

## Qualité des données

| Métrique | Seuil | Description |
|----------|-------|-------------|
| Complétude | > 95% | Pas de valeurs manquantes critiques |
| Unicité | 100% | Pas de doublons |
| Validité | > 98% | Format et type corrects |
| Cohérence | > 95% | Relations entre tables respectées |
| Fraîcheur | < 24h | Données à jour |

---

## Technologies

- **Python 3.11+**
- **Pandas** — Manipulation de données
- **SQLAlchemy** — ORM et connexions bases de données
- **PostgreSQL** — Data warehouse
- **Pytest** — Tests automatisés
- **Docker** — Containerisation
- **Great Expectations** — Validation qualité (optionnel)

---

## Résultats attendus

- [ ] Pipeline ETL fonctionnel et reproductible
- [ ] Tests automatisés avec couverture > 80%
- [ ] Documentation complète
- [ ] Métriques de qualité des données
- [ ] Dashboard de monitoring (optionnel)

---

## Licence

MIT License — voir le fichier LICENSE pour plus de détails.

---

## Auteur

**BIDIGA Imrane** — [GitHub](https://github.com/kouewanbidiga2-bot)
