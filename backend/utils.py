import pandas as pd
from datetime import datetime
from . import schemas
import numpy as np

def parse_excel_file(file_content):
    # Based on our previous analysis, data starts at row 12 (header index 11)
    df = pd.read_excel(file_content, header=12)
    
    transactions = []
    for _, row in df.iterrows():
        # Check if Date is valid
        if pd.isna(row['Date']):
            continue
            
        try:
            if hasattr(row['Date'], 'date'):
                trans_date = row['Date'].date()
            else:
                # Try to parse string date, handle errors
                date_str = str(row['Date']).strip()
                if not date_str or 'Titulaire' in date_str: # Skip rows with non-date content
                    continue
                trans_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
        except (ValueError, TypeError):
            continue # Skip invalid date rows
            
        # Clean data: Replace NaN by None for database compatibility
        debit = row['Débit euros']
        if pd.isna(debit) or (isinstance(debit, str) and not debit.strip()):
            debit = None
        else:
            try:
                debit = float(debit)
            except (ValueError, TypeError):
                debit = None
            
        credit = row['Crédit euros']
        if pd.isna(credit) or (isinstance(credit, str) and not credit.strip()):
            credit = None
        else:
            try:
                credit = float(credit)
            except (ValueError, TypeError):
                credit = None

        # Hierarchical categorization logic
        family, category, subcategory = categorize_transaction(str(row['Libellé']))
            
        transactions.append(schemas.TransactionCreate(
            date=trans_date,
            label=str(row['Libellé']).strip(),
            debit=debit,
            credit=credit,
            family=family,
            category=category,
            subcategory=subcategory
        ))
    return transactions

def categorize_transaction(label: str) -> tuple[str, str, str]:
    label = label.upper()
    
    # 1. Maison
    if any(k in label for k in ["TOTALENERGIES", "EDF", "ENGIE"]):
        return "Maison", "Charges", "Énergie"
    if "SAUR" in label:
        return "Maison", "Charges", "Eau"
    if any(k in label for k in ["ORANGE", "FREE", "SFR", "BOUYGUES", "IMAGINE R", "COMUTITRES", "NAVIGO"]):
        if any(k in label for k in ["NAVIGO", "IMAGINE R"]):
            return "Transports", "Mobilité", "Transports en commun"
        return "Maison", "Charges", "Téléphonie & Internet"
    if "CREDIPAR" in label:
        return "Maison", "Loyer/Prêt", "Prêt Immobilier"
    if any(k in label for k in ["LEROY MERLIN", "CASTORAMA", "BRICO"]):
        return "Maison", "Entretien & Brico", "Bricolage"
    if "FRISQUET" in label:
        return "Maison", "Entretien & Brico", "Maintenance Chauffage"
    
    # 2. Alimentation
    if any(k in label for k in ["SUPERU", "CARREFOUR", "AUCHAN", "MONOPRIX", "LIDL", "ALDI", "PICARD"]):
        return "Alimentation", "Courses", "Supermarché"
    if any(k in label for k in ["BOULANGERIE", "PATISSERIE"]):
        return "Alimentation", "Courses", "Boulangerie"
    if any(k in label for k in ["RESTAURANT", "BISTROT", "MC DONALD'S", "BURGER KING", "KFC", "VERTICAL ART"]):
        return "Alimentation", "Repas Extérieur", "Restaurant"

    # 3. Santé
    if "PHARMACIE" in label:
        return "Santé", "Soins", "Pharmacie"
    if any(k in label for k in ["DOCTOLIB", "CABINET MEDICAL", "MEDECIN", "DENTISTE", "OPTICIEN"]):
        return "Santé", "Soins", "Médecin"
    if any(k in label for k in ["SIACI", "WILLIS TOWERS WATSON", "CPAM"]):
        # Can be income or expense
        if "CPAM" in label:
            return "Santé", "Assurance", "CPAM"
        return "Santé", "Assurance", "Mutuelle"

    # 4. Transports
    if "MMA IARD" in label:
        return "Transports", "Véhicule", "Assurance"
    if any(k in label for k in ["ROOLE", "IDENTICAR"]):
        return "Transports", "Véhicule", "Entretien"
    if "ASF" in label:
        return "Transports", "Mobilité", "Autoroute"

    # 5. Revenus
    if any(k in label for k in ["CAPGEMINI", "SALARY"]):
        return "Revenus", "Travail", "Salaire"
    
    # 6. Épargne & Finance
    if "PEA" in label:
        return "Épargne & Finance", "Placements", "PEA"
    if any(k in label for k in ["1ERE BRIQUE", "COINHOUSE"]):
        return "Épargne & Finance", "Placements", "Crowdfunding"
    if any(k in label for k in ["DIRECTION GENERALE DES FINANCES", "IMPOT TF"]):
        return "Épargne & Finance", "Impôts", "Impôts Locaux"

    # 7. Quotidien / Shopping
    if "AMAZON" in label:
        return "Quotidien", "Shopping", "Amazon"
    if "ORANGE" in label and "MOBILE" in label:
        return "Maison", "Charges", "Téléphonie & Internet"

    # Catch all for income
    if "VIREMENT EN VOTRE FAVEUR" in label:
        return "Revenus", "Remboursements", "Divers"
    
    return "Inconnu", "Inconnu", "Inconnu"
