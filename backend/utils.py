import logging
from datetime import datetime
from . import schemas
import numpy as np
import io

logger = logging.getLogger(__name__)

# Hardened imports with clear error messages
try:
    import pandas as pd
except ImportError:
    logger.error("Pandas is not installed. Please run 'pip install pandas'.")
    raise ImportError("Pandas is required for Excel processing. Run 'pip install pandas'.")

try:
    from dateutil import parser
except ImportError:
    logger.error("python-dateutil is not installed. Please run 'pip install python-dateutil'.")
    raise ImportError("python-dateutil is required for date parsing. Run 'pip install python-dateutil'.")

def parse_excel_file(file_content):
    logger.info("Starting parse_excel_file function.")
    
    # Load entire file without header first to find markers
    try:
        # We use a temporary buffer to avoid issues with reading twice if needed
        content_bytes = file_content.read()
        df_full = pd.read_excel(io.BytesIO(content_bytes), header=None)
        logger.info(f"Full Excel file loaded for marker detection. Shape: {df_full.shape}")
    except ImportError as e:
        error_msg = f"Missing optional dependency for Excel: {str(e)}"
        if 'openpyxl' in str(e):
            error_msg = "The 'openpyxl' library is missing. Please run 'pip install openpyxl' to read .xlsx files."
        elif 'xlrd' in str(e):
            error_msg = "The 'xlrd' library is missing. Please run 'pip install xlrd' to read .xls files."
        logger.error(error_msg)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to read Excel file: {str(e)}")

    # 1. Detect markers
    solde_row_idx = -1
    ops_row_idx = -1
    account_balance = None
    balance_date = None

    for idx, row in df_full.iterrows():
        # Ensure all cells are strings before joining to avoid TypeError
        row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
        
        # Detection of "Solde au"
        if "Solde au" in row_str and solde_row_idx == -1:
            solde_row_idx = idx
            # Extract balance (usually in the next non-empty cell of the same row)
            for cell in row:
                if pd.notna(cell) and isinstance(cell, str) and any(c.isdigit() for c in cell):
                    account_balance = cell
                    logger.info(f"Detected account balance: {account_balance} at row {idx}")
                    break
        
        # Detection of "Liste des opérations"
        if "Liste des opérations" in row_str and ops_row_idx == -1:
            ops_row_idx = idx
            logger.info(f"Detected 'Liste des opérations' at row {idx}")
            break # We found the start of data

    if ops_row_idx == -1:
        logger.error("Marker 'Liste des opérations' not found in Excel file.")
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Format Excel non reconnu : 'Liste des opérations' introuvable.")

    # 2. Reload data with correct header
    header_idx = ops_row_idx + 1
    logger.info(f"Parsing transactions with header at row index {header_idx}")
    df = pd.read_excel(io.BytesIO(content_bytes), header=header_idx)
    
    transactions = []
    for index, row in df.iterrows():
        # Check if Date is valid
        if pd.isna(row['Date']):
            logger.debug(f"Row {index}: Skipping due to missing Date (end of table or spacer).")
            continue
            
        try:
            if hasattr(row['Date'], 'date'):
                trans_date = row['Date'].date()
            else:
                # Try to parse string date, handle errors
                date_str = str(row['Date']).strip()
                if not date_str or any(k in date_str for k in ['Titulaire', 'Date', 'Encours']):
                    logger.debug(f"Row {index}: Skipping non-date content: '{date_str}'.")
                    continue
                trans_date = parser.parse(date_str).date()
        except (ValueError, TypeError, Exception) as e:
            logger.warning(f"Row {index}: Could not parse date '{row['Date']}': {e}. Skipping row.")
            continue
            
        # Clean data: Replace NaN by None for database compatibility
        def parse_amount(val):
            if pd.isna(val) or (isinstance(val, str) and not val.strip()):
                return None
            try:
                if isinstance(val, str):
                    # Handle French format: "1 234,56 €" -> "1234.56"
                    clean_val = val.replace(',', '.').replace('\xa0', '').replace(' ', '').replace('€', '').strip()
                    return float(clean_val)
                return float(val)
            except (ValueError, TypeError):
                return None

        debit = parse_amount(row['Débit euros'])
        credit = parse_amount(row['Crédit euros'])

        label = str(row['Libellé']).strip()
        # Hierarchical categorization logic
        family, category, subcategory = categorize_transaction(label)
            
        transactions.append(schemas.TransactionCreate(
            date=trans_date,
            label=label,
            debit=debit,
            credit=credit,
            family=family,
            category=category,
            subcategory=subcategory
        ))
    
    logger.info(f"Finished parse_excel_file function. Parsed {len(transactions)} transactions.")
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
