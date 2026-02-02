# Data Import Status

## CSV Files for Capital Repair Data

All 14 PFO regions are ready for import:

| # | Region Code | Region Name | Status | CSV Files |
|---|-------------|-------------|--------|-----------|
| 1 | 16 | Республика Татарстан | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 2 | 02 | Республика Башкортостан | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 3 | 12 | Республика Марий Эл | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 4 | 13 | Республика Мордовия | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 5 | 18 | Удмуртская Республика | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 6 | 21 | Чувашская Республика | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 7 | 43 | Кировская область | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 8 | 52 | Нижегородская область | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 9 | 56 | Оренбургская область | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 10 | 58 | Пензенская область | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 11 | 59 | Пермский край | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 12 | 63 | Самарская область | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 13 | 64 | Саратовская область | ✅ Ready | KR 1.1, 1.2, 1.3 |
| 14 | 73 | Ульяновская область | ✅ Ready | KR 1.1, 1.2, 1.3 |

**Total:** All 14 regions ✅

---

## OJF Files (Objects of Housing Fund)

Extracted from archive: `Сведения_об_объектах_жилищного_фонда_на_25-01-2026.tar.gz`

Files located in: `data/ojf_data/`

| # | Region Code | Region Name | OJF Files | Status |
|---|-------------|-------------|-----------|--------|
| 1 | 16 | Республика Татарстан | 5 files | ✅ Ready |
| 2 | 02 | Республика Башкортостан | 5 files | ✅ Ready |
| 3 | 12 | Республика Марий Эл | 1 file | ✅ Ready |
| 4 | 13 | Республика Мордовия | 1 file | ✅ Ready |
| 5 | 18 | Удмуртская Республика | 2 files | ✅ Ready |
| 6 | 21 | Чувашская Республика | 2 files | ✅ Ready |
| 7 | 43 | Кировская область | 2 files | ✅ Ready |
| 8 | 52 | Нижегородская область | 4 files | ✅ Ready |
| 9 | 56 | Оренбургская область | 2 files | ✅ Ready |
| 10 | 58 | Пензенская область | 2 files | ✅ Ready |
| 11 | 59 | Пермский край | 3 files | ✅ Ready |
| 12 | 63 | Самарская область | 4 files | ✅ Ready |
| 13 | 64 | Саратовская область | 2 files | ✅ Ready |
| 14 | 73 | Ульяновская область | 1 file | ✅ Ready |

**Total:** ~36 OJF files for PFO regions ✅

**Purpose:** Links `houseguid` → `OGRN` (management company identifier)

---

## Registry of Information Providers

File: `Реестр поставщиков информации от 2026-02-01.xlsx`

Location: `data/` (to be confirmed)

**Purpose:** Provides contact information for management companies:
- Organization name
- OGRN
- Email (99.5% coverage)
- Phone (97.7% coverage)
- Director name
- Address

**Total organizations:** 204,031 (nationwide)

**Status:** ⏳ Pending import script

---

## Import Sequence

### ✅ Step 1: Install PostgreSQL
- File: `install_postgres.bat`
- Status: Ready

### ✅ Step 2: Setup Database
- File: `setup_database.bat`
- Status: Ready
- Creates 19 tables + views

### ✅ Step 3: Import Capital Repair Data
- File: `import_data.bat`
- Status: Ready
- Imports: Buildings, Lifts, Construction Elements, Services
- Data source: CSV files in `data/regions/`

### ✅ Step 4: Import OJF Data (Building→UK Links)
- File: `import_ojf.bat`
- Status: **CREATED** ✨
- Imports: Management companies + building relationships
- Data source: `data/ojf_data/*.csv`

### ⏳ Step 5: Import Registry Data (UK Contacts)
- File: `import_registry.bat` (to be created)
- Status: Pending
- Imports: Contact information for management companies
- Data source: `Реестр поставщиков информации от 2026-02-01.xlsx`

### ✅ Step 6: Verify Data
- File: `check_data.bat`
- Status: Ready
- Shows: Target buildings with full UK contact info

---

## Estimated Data Volumes

After complete import (all 14 PFO regions):

| Data Type | Estimated Count |
|-----------|----------------|
| Buildings | ~150,000 - 200,000 |
| Buildings with special accounts (UK/TSJ/JSK) | ~30,000 - 40,000 |
| Lifts | ~150,000 - 200,000 |
| Management Companies (UK/TSJ/JSK) | ~3,000 - 5,000 |
| Construction Elements | ~1,500,000 |
| Services | ~1,200,000 |

**Total database size:** ~500 MB - 1 GB

---

## Current Progress

- [x] Project structure created
- [x] Database schema designed (19 tables)
- [x] SQL migrations created
- [x] CSV import script created
- [x] OJF import script created
- [x] All data files collected
- [ ] Registry import script
- [ ] Complete data import test
- [ ] Web interface development

---

## Next Actions

1. **Test OJF Import**
   ```bash
   import_ojf.bat
   ```
   Choose option [1] for Tatarstan test

2. **Create Registry Import Script**
   Parse Excel file and import UK contact information

3. **Test Complete Pipeline**
   Import all data for Tatarstan and verify links

4. **Import All Regions**
   Full import of 14 PFO regions

5. **Develop Web Interface**
   After data verification
