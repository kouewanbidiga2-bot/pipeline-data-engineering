"""
Extracteur de données API

Ce module gère l'extraction de données depuis des API REST.
"""

import logging
from typing import Dict, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class APIExtractor:
    """
    Extracteur de données depuis des API REST.
    
    Attributes:
        base_url (str): URL de base de l'API
        headers (dict): En-têtes HTTP
        timeout (int): Timeout des requêtes
    """
    
    def __init__(self, base_url: str, headers: Optional[Dict] = None, timeout: int = 30):
        """
        Initialise l'extracteur API.
        
        Args:
            base_url: URL de base de l'API
            headers: En-têtes HTTP personnalisés
            timeout: Timeout des requêtes en secondes
        """
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.timeout = timeout
    
    def extract(self, endpoint: str = "", params: Optional[Dict] = None) -> Optional[pd.DataFrame]:
        """
        Extrait des données depuis un endpoint API.
        
        Args:
            endpoint: Endpoint de l'API
            params: Paramètres de requête
            
        Returns:
            pd.DataFrame: Données extraites ou None en cas d'erreur
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"Extraction depuis {url}")
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Gérer différents formats de réponse
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Chercher une liste dans la réponse
                for key, value in data.items():
                    if isinstance(value, list):
                        df = pd.DataFrame(value)
                        break
                else:
                    df = pd.DataFrame([data])
            else:
                logger.error(f"Format de réponse non supporté: {type(data)}")
                return None
            
            logger.info(f"  -> {len(df)} enregistrements extraits")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête API: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la réponse: {e}")
            return None
    
    def extract_paginated(self, endpoint: str, page_param: str = 'page',
                         limit_param: str = 'limit', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Extrait des données paginées depuis une API.
        
        Args:
            endpoint: Endpoint de l'API
            page_param: Nom du paramètre de pagination
            limit_param: Nom du paramètre de limite
            limit: Nombre d'éléments par page
            
        Returns:
            pd.DataFrame: Données extraites ou None
        """
        all_data = []
        page = 1
        
        while True:
            params = {page_param: page, limit_param: limit}
            df = self.extract(endpoint, params)
            
            if df is None or len(df) == 0:
                break
            
            all_data.append(df)
            
            if len(df) < limit:
                break
            
            page += 1
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        
        return None
