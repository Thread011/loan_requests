# Système de Traitement de Prêts Immobiliers

## Description
Système complet de traitement automatisé des demandes de prêts immobiliers intégrant l'évaluation de propriété, l'analyse de solvabilité et la prise de décision automatisée.

## Architecture du Système

### Services Principaux
1. **Service d'Extraction (Port: 8000)**
   - Conversion des demandes textuelles en format JSON structuré
   - Extraction des informations clés (coordonnées, montants, etc.)

2. **Service de Solvabilité (Port: 8001)**
   - Évaluation de la solvabilité des demandeurs
   - Calcul du score de crédit (base 1000 points)
   - Analyse des antécédents financiers

3. **Service d'Évaluation Immobilière (Port: 8003)**
   - Estimation de la valeur des biens
   - Vérification de la conformité légale
   - Analyse de l'état du bien
   - Base de données du marché immobilier intégrée

4. **Service de Décision (Port: 8004)**
   - Analyse complète des risques
   - Application des politiques institutionnelles
   - Calcul des taux d'intérêt
   - Génération des décisions motivées

5. **API REST (Port: 5000)**
   - Point d'entrée principal du système
   - Orchestration des services via ServiceComposite
   - Gestion des sessions clients

## Installation

### Prérequis
```bash
python -m pip install spyne suds-jurko flask flask-cors watchdog twisted lxml
```

### Démarrage
```bash
# Démarrer chaque service dans un terminal séparé
python services/extractService.py         # Port 8000
python services/checkSolvabService.py     # Port 8001
python services/propEvalService.py        # Port 8003
python services/decisionService.py        # Port 8004
python api/api_service.py                 # Port 5000
```