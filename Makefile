.PHONY: help install test run docker-build docker-run clean

help:
	@echo "Commandes disponibles:"
	@echo "  make install       - Installer les dépendances Python"
	@echo "  make test          - Lancer les tests unitaires"
	@echo "  make run           - Lancer le pipeline complet"
	@echo "  make docker-build  - Builder l'image Docker"
	@echo "  make docker-run    - Lancer le pipeline avec Docker"
	@echo "  make clean         - Nettoyer les fichiers temporaires"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

run:
	python src/pipeline.py --config config.yaml

docker-build:
	docker build -t data-pipeline .

docker-run:
	docker-compose up --build

clean:
	rm -rf __pycache__ .pytest_cache *.pyc .coverage htmlcov logs/*.log
	rm -rf data/processed/* data/warehouse/*
