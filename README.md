
# Fiindo Recruitment Challenge – ETL Solution

This repository contains my implementation of the **Fiindo Recruitment Challenge**, which requires building a complete ETL (Extract–Transform–Load) workflow:

1. **Fetch** financial data from the Fiindo API  
2. **Transform & calculate** ticker statistics and industry aggregations  
3. **Store** processed results into an SQLite database  

The solution is fully structured, documented, and ready for review.

---

# 📂 Project Structure

```
fiindo-recruitment-challenge/
│
├── src/
│   ├── step1_fetch.py              # Fetches data from Fiindo API
│   ├── step2_transform.py          # Calculates all statistics
│   ├── step3_load.py               # Stores data in SQLite DB
│   ├── speedboost.py               # enable Speedboost
│   ├── check_database.py           # Checked Database  
│   ├── models.py                   # SQLAlchemy models
│
├── tests/
│   ├── __init__.py         
│   ├── test_step1_fetch.py         # Testing Step1       
│   ├── test_step2_transform.py     # Testing Step2          
│   ├── test_step3_load.py          # Testing Step3     
│   ├── run_tests.py                # Run all 3 Tests         
│
├── data/                           # JSON input/output data
├── db/                             # SQLite database directory
├── alembic/                        # Database migrations
│   ├── versions/  
│   ├── env.py
│   ├── README
│   ├── script.py.mako  
│
├── README.md
├── README_Challenge.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env                            # Contains credentials
```

---

# 🚀 Features

### ✔ Fully working ETL pipeline  
### ✔ Automatic statistics calculation:  
- PE Ratio  
- Revenue Growth (quarter vs quarter)  
- Net Income TTM  
- Debt-to-Equity Ratio  

### ✔ Industry aggregations:  
- Average PE Ratio  
- Average Revenue Growth  
- Total Revenue  
- Ticker count  

### ✔ SQLite database storage  
### ✔ SQLAlchemy ORM  
### ✔ Optional Docker support  
### ✔ Clear logs & error handling

---

# 🔧 Setup Instructions

## 1️⃣ Install Python Dependencies

```bash
  pip install -r requirements.txt
```

---

## 2️⃣ Create `.env` file

Your `.env` must contain:

```
FIRST_NAME=yourfirstname
LAST_NAME=yourlastname
```

Authentication is:

```
Authorization: Bearer {FIRST_NAME}.{LAST_NAME}
```

---

## 3️⃣ Ensure folders exist

```bash
  mkdir -p data db
```

---

# ▶️ How to Run the ETL Pipeline

Run **each step in order**:

---

## STEP 1 – Fetch API Data

```bash
  python src/step1_fetch.py
```

This will:

✔ Authenticate with the Fiindo API  
✔ Fetch all required financial data  
✔ Save raw JSON → `data/financial_data_YYYYMMDD_HHMMSS.json`

---

## STEP 2 – Transform & Calculate Metrics

```bash
  python src/step2_transform.py
```

This will:

✔ Load the latest financial data  
✔ Calculate all ticker-level statistics  
✔ Calculate industry-level aggregations  
✔ Save results into:

```
data/ticker_statistics_*.json
data/industry_aggregation_*.json
```

---

## STEP 3 – Store Data in SQLite Database

```bash
  python src/step3_load.py
```

This will:

✔ Create database (if not exists)  
✔ Populate ticker_statistics table  
✔ Populate industry_aggregation table  
✔ Display database summary  
✔ Optionally create a DB backup  

Database file:

```
db/fiindo_challenge.db
```

---

# 🐳 Running with Docker (Optional)

## Build the container:

```bash
  docker build -t fiindo-etl .
```

## Run with docker-compose:

```bash
  docker-compose up --build
```

This will:

✔ Install dependencies  
✔ Run the ETL pipeline  
✔ Persist data in mounted volumes  

---

# 🧪 (Bonus) Unit Tests

Run tests:

```bash
  pytest -v
```

The tests cover:

- ETL steps  
- Transform logic  
- Database storage utilities  

---

# 📊 How to Inspect the Database

Open SQLite:

```bash
  sqlite3 db/fiindo_challenge.db
```

Useful commands:

```sql
.tables
SELECT * FROM ticker_statistics LIMIT 5;
SELECT * FROM industry_aggregation;
```

---

# 📝 Notes

- Only tickers from these industries are processed:  
  - Banks – Diversified  
  - Software – Application  
  - Consumer Electronics  
- All other industries are ignored (per challenge specification).  
- All paths are configured to work whether executed from project root or `/src`.

---

If you have any questions, feel free to ask!
