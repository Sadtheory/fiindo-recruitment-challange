# Fiindo Recruitment Challenge – ETL Pipeline

## Overview
This project implements a full ETL (Extract–Transform–Load) workflow for financial market data provided by the **Fiindo API**.  
The pipeline retrieves raw ticker data, processes financial metrics, aggregates industry-level statistics, and stores everything in a **SQLite database**.

The repository is structured for:
- **Docker-first execution** (empfohlen)
- **Optional local CLI execution** der ETL-Schritte
- **Full automated unit testing**
- **Modular ETL pipeline**: Step 1 → Step 2 → Step 3 → Database inspection

---

# 1. Project Structure
```text
.
fiindo-recruitment-challenge/
├── src/                          # Core pipeline implementation
│   ├── step1_fetch.py            # Extract: Fetch data from Fiindo API
│   ├── step2_transform.py        # Transform: Calculate financial metrics
│   ├── step3_load.py             # Load: Insert data into SQLite
│   ├── speedboost.py             # Optional: Optimize API requests with speed boost
│   ├── check_database.py         # Database verification and summary tools
│   ├── models.py                 # SQLAlchemy ORM models
│
├── tests/                        # Comprehensive test suite
│   ├── test_step1_fetch.py       # 23 tests for data extraction
│   ├── test_step2_transform.py   # 20 tests for data transformation
│   ├── test_step3_load.py        # 15 tests for database operations
│   └── run_tests.py              # Single command to run all tests
│
├── data/                         # JSON data storage (gitignored)
├── db/                           # SQLite database files (gitignored)
├── alembic/                      # Database migration utilities
│
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Multi-service orchestration
├── run_pipeline.py               # Main pipeline orchestration script
├── requirements.txt              # Python dependencies
├── .env                          # Environment configuration
├── .gitignore                    # Git exclusion rules
├── README.md                     # This documentation
└── README_Challenge.md           # Original challenge requirements
```

---

# 2. Setup & Installation

## 2.1 Requirements
- Python 3.10+
- pip
- Docker (optional but recommended)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

# 3. Running the ETL Pipeline

# 3.1 Recommended Method: Docker-based Execution
Docker runs the entire pipeline in isolated containers.

### Build containers
```bash
docker compose build
```

### Run the full pipeline
```bash
docker compose up
```

### Run individual steps (optional)
```bash
docker compose run step1-fetch
docker compose run step2-transform
docker compose run step3-load
```

---

# 3.2 Alternative: Running Pipeline Locally (Without Docker)

### Step 1 — Fetch raw financial data
```bash
python src/step1_fetch.py
```

### Step 2 — Transform raw data into statistics
```bash
python src/step2_transform.py
```

### Step 3 — Load data into SQLite
```bash
python src/step3_load.py
```

### Optional: Speed-optimized fetching 
```bash
python src/speedboost.py
```

### View database summary
```bash
python src/check_database.py
```

---

# 4. Running the Pipeline Controller (`run_pipeline.py`)

The pipeline controller orchestrates all steps automatically.

### Run full ETL
```bash
python run_pipeline.py
```

### Start pipeline at a specific point
This is helpful if, for example, Step 1 has already been executed.

```bash
python run_pipeline.py --starting_at step2
```

Valid values:
- `step1`
- `step2`
- `step3`

---

# 5. Database Structure (SQLite)

The database is located at:

```
db/fiindo_challenge.db
```

The pipeline generates three tables:

---

## 5.1 ticker_statistics
Contains calculated financial figures for individual stocks.

| Column             | Description |
|-------------------|-------------|
| symbol            | Ticker Symbol |
| name              | Full company name |
| industry          | Industry group |
| pe_ratio          | Price-to-Earnings (last quarter) |
| revenue_growth    | Q/Q Revenue Growth (%) |
| net_income_ttm    | Trailing Twelve Months Net Income |
| debt_ratio        | Debt-to-Equity (last year) |
| price             | Latest available stock price |
| revenue_current   | Latest revenue value |
| last_updated      | Timestamp |
| is_active         | Boolean flag |

---

## 5.2 industry_aggregation
Aggregated key figures across all tickers per industry.

| Column                | Description |
|-----------------------|-------------|
| industry             | Industry Name |
| avg_pe_ratio         | Mean PE Ratio |
| avg_revenue_growth   | Mean Rev. Growth |
| sum_revenue          | Total revenue |
| ticker_count         | Number of tickers in this industry |
| last_updated         | Timestamp |

---

## 5.3 alembic_version
Migration tables managed by Alembic.

---

# 6. Example Output (from check_database.py)

### Ticker Examples
```
symbol   industry               PE     Growth   NetIncome     DebtRatio
0Q1F.L   Banks - Diversified    14.31   1.46    56533000000   1.32
XM.US    Software - Application -10.55 -71.91   -1028117000   0.15
ZI.US    Software - Application 36.15   0.33    89200000      0.82
```

### Industry Aggregation Example
```
Banks - Diversified:
  Count: 66
  Avg PE: 62.51
  Avg Growth: 46.13%
  Sum Revenue: 1.44T
```

---

# 7. Unit Testing

All tests can be performed using a single script:

```bash
python tests/run_tests.py
```

### Test Coverage:

| Area   | Tests                 |
|--------|-----------------------|
| Step 1 | 23 Tests              |
| Step 2 | 20 Tests              |
| Step 3 | 15 Tests              |
| Total  | 58 Tests – all passed |

The tests check, among other things:

- API Header Logik  
- Extraction Edge Cases  
- All Metric Calculations  
- JSON Loading  
- Database Inserts & Aggregations  
- Pipeline Integration  

---

# 8. Environment Variables
Set in `.env`:

```
FIINDO_FIRST_NAME=John
FIINDO_LAST_NAME=Doe
```

Used for API authentication:
```
Authorization: Bearer {first}.{last}
```

---

# 9. Troubleshooting

### Data directory missing
→ Step 1 not executed  
→  Or folder structure not present

### Models not found
→ Make sure that `src/` is used as the working directory.

### API returns no symbols
→ Possibly incorrect authorization header

---

# 10. License
This project is part of a technical application task.

Please use for private purposes only.


---

**Thank you for reviewing this challenge solution.**  
For any questions, feel free to reach out.  
