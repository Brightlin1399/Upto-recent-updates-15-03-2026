"""
Shared seed data for ~100 MDGM rows: regions, countries, brands, SKUs, and sku_mdgm_master rows.
Used by seed_test_data.py and export_mdgm_to_excel.py.
"""

# Regions: code, name
REGIONS = [
    ("APAC", "APAC"),
    ("EMEA", "EMEA"),
    ("LATAM", "LATAM"),
    ("NA", "North America"),
]

# Countries: (code, name, region)
COUNTRIES = [
    ("IN", "India", "APAC"),
    ("JP", "Japan", "APAC"),
    ("CN", "China", "APAC"),
    ("AU", "Australia", "APAC"),
    ("KR", "South Korea", "APAC"),
    ("TH", "Thailand", "APAC"),
    ("AL", "Albania", "EMEA"),
    ("BA", "Bosnia and Herzegovina", "EMEA"),
    ("DE", "Germany", "EMEA"),
    ("FR", "France", "EMEA"),
    ("UK", "United Kingdom", "EMEA"),
    ("ES", "Spain", "EMEA"),
    ("IT", "Italy", "EMEA"),
    ("BR", "Brazil", "LATAM"),
    ("MX", "Mexico", "LATAM"),
    ("AR", "Argentina", "LATAM"),
    ("US", "United States", "NA"),
    ("CA", "Canada", "NA"),
]

# Brand -> therapeutic area
BRANDS_TA = [
    ("EUTHYROX", "CMC"),
    ("BAVENCIO", "Fertility & NDD"),
    ("Dart", "Cardiology"),
    ("Crocin", "OTC"),
    ("LENVIMA", "Oncology"),
    ("KEYTRUDA", "Oncology"),
    ("JANUVIA", "Diabetes"),
    ("GARDASIL", "Vaccines"),
]

# SKU id, name (unique SKUs referenced in MDGM)
SKUS = [
    ("SKU-001", "Test SKU 1"),
    ("SKU-002", "Test SKU 2"),
    ("SKU-003", "Test SKU 3"),
    ("SKU-004", "Test SKU 4"),
    ("SKU-005", "Test SKU 5"),
    ("SKU-IN-001", "India SKU 1"),
    ("SKU-IN-002", "India SKU 2"),
    ("SKU-JP-001", "Japan SKU 1"),
    ("SKU-JP-002", "Japan SKU 2"),
    ("SKU-CN-001", "China SKU 1"),
    ("SKU-AU-001", "Australia SKU 1"),
    ("SKU-KR-001", "Korea SKU 1"),
    ("SKU-TH-001", "Thailand SKU 1"),
    ("SKU-DE-001", "Germany SKU 1"),
    ("SKU-DE-002", "Germany SKU 2"),
    ("SKU-FR-001", "France SKU 1"),
    ("SKU-UK-001", "UK SKU 1"),
    ("SKU-ES-001", "Spain SKU 1"),
    ("SKU-IT-001", "Italy SKU 1"),
    ("SKU-BR-001", "Brazil SKU 1"),
    ("SKU-MX-001", "Mexico SKU 1"),
    ("SKU-AR-001", "Argentina SKU 1"),
    ("SKU-US-001", "US SKU 1"),
    ("SKU-US-002", "US SKU 2"),
    ("SKU-CA-001", "Canada SKU 1"),
    ("SKU-NO-HISTORY", "SKU with MDGM only (no history)"),
    ("SKU-EUTHYROX-01", "EUTHYROX 25mcg"),
    ("SKU-EUTHYROX-02", "EUTHYROX 50mcg"),
    ("SKU-CROCIN-01", "Crocin 500mg"),
    ("SKU-LENVIMA-01", "LENVIMA 4mg"),
    ("SKU-JANUVIA-01", "JANUVIA 100mg"),
]

# MDGM rows: sku_id, country, region, therapeutic_area, brand, channel, price_type, current_price_eur, marketed_status, currency
# ~100 rows with variety across regions, countries, brands, TAs
MDGM_ROWS = [
    # APAC - EUTHYROX (CMC)
    ("SKU-001", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 100.0, "Marketed", "EUR"),
    ("SKU-002", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 98.0, "Marketed", "EUR"),
    ("SKU-IN-001", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 105.0, "Marketed", "EUR"),
    ("SKU-001", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "List Price", 2.11, "Marketed", "EUR"),
    ("SKU-002", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "List Price", 2.05, "Marketed", "EUR"),
    ("SKU-001", "IN", "APAC", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 102.0, "Marketed", "EUR"),
    ("SKU-EUTHYROX-01", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 45.0, "Marketed", "EUR"),
    ("SKU-EUTHYROX-02", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 52.0, "Marketed", "EUR"),
    ("SKU-NO-HISTORY", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 50.0, "Marketed", "EUR"),
    ("SKU-JP-001", "JP", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 120.0, "Marketed", "JPY"),
    ("SKU-JP-002", "JP", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 115.0, "Marketed", "JPY"),
    ("SKU-JP-001", "JP", "APAC", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 118.0, "Marketed", "JPY"),
    ("SKU-CN-001", "CN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 88.0, "Marketed", "CNY"),
    ("SKU-AU-001", "AU", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 95.0, "Marketed", "AUD"),
    ("SKU-KR-001", "KR", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 92.0, "Marketed", "KRW"),
    ("SKU-TH-001", "TH", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 78.0, "Marketed", "THB"),
    # APAC - Crocin (OTC)
    ("SKU-CROCIN-01", "IN", "APAC", "OTC", "Crocin", "Retail", "NSP Minimum", 3.50, "Marketed", "EUR"),
    ("SKU-CROCIN-01", "IN", "APAC", "OTC", "Crocin", "Pharmacy", "NSP Minimum", 3.20, "Marketed", "EUR"),
    ("SKU-CROCIN-01", "JP", "APAC", "OTC", "Crocin", "Retail", "NSP Minimum", 4.00, "Marketed", "JPY"),
    ("SKU-003", "TH", "APAC", "OTC", "Crocin", "Retail", "NSP Minimum", 2.80, "Marketed", "THB"),
    # APAC - LENVIMA (Oncology)
    ("SKU-LENVIMA-01", "IN", "APAC", "Oncology", "LENVIMA", "Retail", "NSP Minimum", 450.0, "Marketed", "EUR"),
    ("SKU-LENVIMA-01", "JP", "APAC", "Oncology", "LENVIMA", "Retail", "NSP Minimum", 480.0, "Marketed", "JPY"),
    ("SKU-004", "AU", "APAC", "Oncology", "LENVIMA", "Retail", "NSP Minimum", 420.0, "Marketed", "AUD"),
    # APAC - JANUVIA (Diabetes)
    ("SKU-JANUVIA-01", "IN", "APAC", "Diabetes", "JANUVIA", "Retail", "NSP Minimum", 28.0, "Marketed", "EUR"),
    ("SKU-JANUVIA-01", "IN", "APAC", "Diabetes", "JANUVIA", "Pharmacy", "NSP Minimum", 26.0, "Marketed", "EUR"),
    ("SKU-JANUVIA-01", "CN", "APAC", "Diabetes", "JANUVIA", "Retail", "NSP Minimum", 25.0, "Marketed", "CNY"),
    # EMEA - EUTHYROX
    ("SKU-DE-001", "DE", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 110.0, "Marketed", "EUR"),
    ("SKU-DE-002", "DE", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 108.0, "Marketed", "EUR"),
    ("SKU-DE-001", "DE", "EMEA", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 109.0, "Marketed", "EUR"),
    ("SKU-FR-001", "FR", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 105.0, "Marketed", "EUR"),
    ("SKU-UK-001", "UK", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 98.0, "Marketed", "GBP"),
    ("SKU-ES-001", "ES", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 102.0, "Marketed", "EUR"),
    ("SKU-IT-001", "IT", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 104.0, "Marketed", "EUR"),
    ("SKU-001", "AL", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 72.0, "Marketed", "EUR"),
    ("SKU-002", "BA", "EMEA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 68.0, "Marketed", "BAM"),
    # EMEA - BAVENCIO (Fertility & NDD)
    ("SKU-005", "DE", "EMEA", "Fertility & NDD", "BAVENCIO", "Retail", "NSP Minimum", 3200.0, "Marketed", "EUR"),
    ("SKU-005", "FR", "EMEA", "Fertility & NDD", "BAVENCIO", "Retail", "NSP Minimum", 3150.0, "Marketed", "EUR"),
    ("SKU-005", "UK", "EMEA", "Fertility & NDD", "BAVENCIO", "Retail", "NSP Minimum", 2980.0, "Marketed", "GBP"),
    # EMEA - Dart (Cardiology)
    ("SKU-001", "DE", "EMEA", "Cardiology", "Dart", "Retail", "NSP Minimum", 85.0, "Marketed", "EUR"),
    ("SKU-002", "FR", "EMEA", "Cardiology", "Dart", "Retail", "NSP Minimum", 82.0, "Marketed", "EUR"),
    ("SKU-003", "UK", "EMEA", "Cardiology", "Dart", "Pharmacy", "NSP Minimum", 78.0, "Marketed", "GBP"),
    # EMEA - KEYTRUDA (Oncology)
    ("SKU-004", "DE", "EMEA", "Oncology", "KEYTRUDA", "Retail", "NSP Minimum", 5200.0, "Marketed", "EUR"),
    ("SKU-004", "FR", "EMEA", "Oncology", "KEYTRUDA", "Retail", "NSP Minimum", 5100.0, "Marketed", "EUR"),
    # EMEA - Crocin (OTC)
    ("SKU-CROCIN-01", "DE", "EMEA", "OTC", "Crocin", "Retail", "NSP Minimum", 4.20, "Marketed", "EUR"),
    ("SKU-CROCIN-01", "UK", "EMEA", "OTC", "Crocin", "Retail", "NSP Minimum", 3.80, "Marketed", "GBP"),
    # LATAM - EUTHYROX
    ("SKU-BR-001", "BR", "LATAM", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 65.0, "Marketed", "BRL"),
    ("SKU-BR-001", "BR", "LATAM", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 63.0, "Marketed", "BRL"),
    ("SKU-MX-001", "MX", "LATAM", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 58.0, "Marketed", "MXN"),
    ("SKU-AR-001", "AR", "LATAM", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 55.0, "Marketed", "ARS"),
    # LATAM - JANUVIA
    ("SKU-JANUVIA-01", "BR", "LATAM", "Diabetes", "JANUVIA", "Retail", "NSP Minimum", 22.0, "Marketed", "BRL"),
    ("SKU-JANUVIA-01", "MX", "LATAM", "Diabetes", "JANUVIA", "Retail", "NSP Minimum", 24.0, "Marketed", "MXN"),
    # LATAM - LENVIMA
    ("SKU-LENVIMA-01", "BR", "LATAM", "Oncology", "LENVIMA", "Retail", "NSP Minimum", 380.0, "Marketed", "BRL"),
    ("SKU-LENVIMA-01", "AR", "LATAM", "Oncology", "LENVIMA", "Retail", "NSP Minimum", 395.0, "Marketed", "ARS"),
    # LATAM - GARDASIL (Vaccines)
    ("SKU-001", "BR", "LATAM", "Vaccines", "GARDASIL", "Retail", "NSP Minimum", 145.0, "Marketed", "BRL"),
    ("SKU-002", "MX", "LATAM", "Vaccines", "GARDASIL", "Retail", "NSP Minimum", 138.0, "Marketed", "MXN"),
    # NA - EUTHYROX
    ("SKU-US-001", "US", "NA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 125.0, "Marketed", "USD"),
    ("SKU-US-002", "US", "NA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 122.0, "Marketed", "USD"),
    ("SKU-US-001", "US", "NA", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 120.0, "Marketed", "USD"),
    ("SKU-US-001", "US", "NA", "CMC", "EUTHYROX", "Retail", "List Price", 3.50, "Marketed", "USD"),
    ("SKU-CA-001", "CA", "NA", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 115.0, "Marketed", "CAD"),
    ("SKU-CA-001", "CA", "NA", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 112.0, "Marketed", "CAD"),
    # NA - KEYTRUDA
    ("SKU-004", "US", "NA", "Oncology", "KEYTRUDA", "Retail", "NSP Minimum", 5500.0, "Marketed", "USD"),
    ("SKU-004", "CA", "NA", "Oncology", "KEYTRUDA", "Retail", "NSP Minimum", 5200.0, "Marketed", "CAD"),
    # NA - JANUVIA
    ("SKU-JANUVIA-01", "US", "NA", "Diabetes", "JANUVIA", "Retail", "NSP Minimum", 32.0, "Marketed", "USD"),
    ("SKU-JANUVIA-01", "US", "NA", "Diabetes", "JANUVIA", "Pharmacy", "NSP Minimum", 30.0, "Marketed", "USD"),
    ("SKU-JANUVIA-01", "CA", "NA", "Diabetes", "JANUVIA", "Retail", "NSP Minimum", 29.0, "Marketed", "CAD"),
    # NA - BAVENCIO
    ("SKU-005", "US", "NA", "Fertility & NDD", "BAVENCIO", "Retail", "NSP Minimum", 3500.0, "Marketed", "USD"),
    ("SKU-005", "CA", "NA", "Fertility & NDD", "BAVENCIO", "Retail", "NSP Minimum", 3380.0, "Marketed", "CAD"),
    # NA - GARDASIL
    ("SKU-001", "US", "NA", "Vaccines", "GARDASIL", "Retail", "NSP Minimum", 185.0, "Marketed", "USD"),
    ("SKU-002", "US", "NA", "Vaccines", "GARDASIL", "Pharmacy", "NSP Minimum", 178.0, "Marketed", "USD"),
    ("SKU-001", "CA", "NA", "Vaccines", "GARDASIL", "Retail", "NSP Minimum", 165.0, "Marketed", "CAD"),
    # NA - Crocin
    ("SKU-CROCIN-01", "US", "NA", "OTC", "Crocin", "Retail", "NSP Minimum", 5.20, "Marketed", "USD"),
    ("SKU-CROCIN-01", "CA", "NA", "OTC", "Crocin", "Retail", "NSP Minimum", 4.90, "Marketed", "CAD"),
    # Extra rows to reach ~100
    ("SKU-IN-002", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 107.0, "Marketed", "EUR"),
    ("SKU-IN-002", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "List Price", 2.25, "Marketed", "EUR"),
    ("SKU-003", "IN", "APAC", "CMC", "EUTHYROX", "Retail", "NSP Minimum", 99.0, "Marketed", "EUR"),
    ("SKU-004", "IN", "APAC", "Oncology", "LENVIMA", "Pharmacy", "NSP Minimum", 455.0, "Marketed", "EUR"),
    ("SKU-005", "DE", "EMEA", "Fertility & NDD", "BAVENCIO", "Pharmacy", "NSP Minimum", 3180.0, "Marketed", "EUR"),
    ("SKU-001", "ES", "EMEA", "Cardiology", "Dart", "Retail", "NSP Minimum", 80.0, "Marketed", "EUR"),
    ("SKU-002", "IT", "EMEA", "Cardiology", "Dart", "Retail", "NSP Minimum", 83.0, "Marketed", "EUR"),
    ("SKU-003", "BR", "LATAM", "OTC", "Crocin", "Retail", "NSP Minimum", 2.90, "Marketed", "BRL"),
    ("SKU-002", "US", "NA", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 121.0, "Marketed", "USD"),
    ("SKU-003", "JP", "APAC", "OTC", "Crocin", "Pharmacy", "NSP Minimum", 4.10, "Marketed", "JPY"),
    ("SKU-DE-002", "DE", "EMEA", "CMC", "EUTHYROX", "Retail", "List Price", 2.85, "Marketed", "EUR"),
    ("SKU-FR-001", "FR", "EMEA", "CMC", "EUTHYROX", "Pharmacy", "NSP Minimum", 106.0, "Marketed", "EUR"),
    ("SKU-001", "CN", "APAC", "OTC", "Crocin", "Retail", "NSP Minimum", 2.50, "Marketed", "CNY"),
    ("SKU-002", "AU", "APAC", "Diabetes", "JANUVIA", "Retail", "NSP Minimum", 27.0, "Marketed", "AUD"),
]
