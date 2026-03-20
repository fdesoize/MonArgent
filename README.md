# MonArgent 💰

MonArgent est une application de gestion de finances personnelles avancée, conçue pour analyser vos exports bancaires Excel et vous offrir une vision claire et granulaire de votre budget.

## 🚀 Fonctionnalités Majeures

### 📊 Analyse & Visualisation
- **Dashboard Analytique** : Une vue en colonnes séparant l'analyse visuelle (Donut Chart) du détail des opérations.
- **Vision Mensuelle** : Sélecteur de mois dynamique pour isoler vos finances période par période.
- **Analyse de Tendance** : Graphique de barres comparant Revenus vs Dépenses sur les 6 derniers mois.
- **Pagination Optimisée** : Navigation fluide avec 25 transactions par page pour une performance maximale.

### 🗂️ Catégorisation Hiérarchique (3 Niveaux)
Moteur de règles intelligent classant automatiquement vos transactions selon une structure précise :
1.  **Famille** (ex: Maison, Alimentation, Santé, Transports)
2.  **Catégorie** (ex: Charges, Courses, Soins, Véhicule)
3.  **Sous-catégorie** (ex: Énergie, Supermarché, Pharmacie, Assurance)

### 📥 Gestion des Données
- **Importation Excel** : Support natif des exports bancaires avec nettoyage automatique des données.
- **Recherche Globale** : Filtre instantané par enseigne, catégorie ou montant.
- **Réinitialisation** : Bouton de vidage complet de la base de données pour repartir à zéro.

## 🏗️ Architecture Technique

*   **Frontend** : React 18 (TypeScript) + Vite
    *   **Recharts** : Visualisations financières (Donut & Bar Charts).
    *   **Date-fns** : Gestion avancée des dates et de la localisation française.
    *   **Lucide React** : Iconographie moderne et épurée.
*   **Backend** : FastAPI (Python 3.10+)
    *   **Pandas** : Moteur de traitement de données haute performance.
    *   **SQLAlchemy** : ORM pour la persistance des données.
    *   **SQLite** : Base de données locale sécurisée.

## 🛠️ Installation et Lancement

### 1. Lancer le Backend
```bash
# Depuis la racine du projet
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 2. Lancer le Frontend
```bash
# Depuis la racine du projet
cd frontend
npm install
npm run dev
```
*Accédez à l'interface sur [http://localhost:5173](http://localhost:5173)*

## 📂 Structure du Projet

```text
MonArgent/
├── backend/            # API & Moteur de règles (FastAPI)
│   ├── models.py       # Schéma de base de données (3 niveaux de catégories)
│   ├── utils.py        # Logique de parsing & Moteur de catégorisation
│   └── main.py         # Endpoints API & Middleware CORS
├── frontend/           # Interface Utilisateur (React)
│   ├── src/
│   │   ├── App.tsx     # Dashboard complet (Stats, Charts, Table)
│   │   └── App.css     # Design System (Layout Sidebar, Responsive)
├── data/               # Dossier pour vos fichiers d'extraction Excel
└── README.md           # Cette documentation
```
