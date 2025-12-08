# step3_data_storage.py
# ---------------------
# Step 3: Data Storage
#
# This module is responsible for:
#  - loading the JSON outputs produced by Step 2
#  - connecting to the SQLite database
#  - creating tables if needed
#  - inserting/updating ticker-level and industry-level records
#  - providing a small CLI-driven backup and summary
#
# Author: Cyn
# Date: 2025-12-08
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

sys.path.append('')  # ensure current working directory is in import path

try:
    # Import SQLAlchemy models (Base and mapped classes).
    # These classes are expected to be defined without modification in models.py.
    from models import Base, TickerStatistics, IndustryAggregation
    print("✅ Database models imported successfully")
except ImportError as e:
    # If importing fails, fail fast with a clear user message.
    print(f"❌ Error importing database models: {e}")
    print("Please ensure models.py is in the same folder as this script (src/), or adjust sys.path.")
    sys.exit(1)


class DataStorage:
    """
    Encapsulates database access and operations.

    Responsibilities:
      - create database/tables
      - connect / disconnect
      - store ticker statistics
      - store industry aggregations
      - load the latest JSON files produced by the transform step
      - display a quick database summary
      - create backups (copy the SQLite file)

    IMPORTANT PATH NOTE:
      - We detect the SQLite database file path automatically so the script can run
        both from the project root and from src/ without manual edits.
      - The detection strategy checks:
          1) db/fiindo_challenge.db   (when running from project root)
          2) ../db/fiindo_challenge.db (when running from src/)
        If neither exists, the code will create db/ and use db/fiindo_challenge.db.
    """

    def __init__(self, database_url: str = "sqlite:///db/fiindo_challenge.db"):
        """
        Initialize the DataStorage.

        The argument `database_url` is the default value used when invoked without parameters.
        We resolve the actual path to the SQLite file and rebuild the database_url accordingly.
        """
        # --- Automatic database path resolution (robust for src/ or project root) ---
        # Possible relative locations where the DB file might live depending on cwd:
        possible_db_paths = [
            Path("db/fiindo_challenge.db"),    # expected when run from project root
            Path("../db/fiindo_challenge.db")  # expected when run from src/
        ]

        # Choose the first existing path, or default to the first (create if missing)
        existing = next((p for p in possible_db_paths if p.exists()), None)
        if existing:
            # If a file already exists, use the path that points to it
            selected_path = existing
        else:
            # If no existing file, we prefer to create db/fiindo_challenge.db under cwd
            # which keeps behavior consistent and predictable.
            selected_path = possible_db_paths[0]
            selected_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert the chosen Path into a SQLite URL that SQLAlchemy accepts.
        # For relative paths, SQLAlchemy wants "sqlite:///relative/path.db".
        resolved_url = f"sqlite:///{selected_path.as_posix()}"

        # Explicitly store resolved values for use by other methods and for clearer debugging
        self.database_path = selected_path  # Path object to the DB file we will use/create
        self.database_url = resolved_url    # SQLAlchemy-compatible URL

        # Create the engine using the resolved URL
        # (we deliberately keep echo=False to match original behavior)
        self.engine = create_engine(self.database_url, echo=False)

        # Session factory (SQLAlchemy ORM)
        self.Session = sessionmaker(bind=self.engine)
        self.session = None

        # Print helpful debug info so the user can see which DB path is used
        print(f"ℹ️  Using database URL: {self.database_url}")
        print(f"ℹ️  Underlying DB file path: {self.database_path.resolve()}")

    def create_database(self):
        """Create database tables using SQLAlchemy models (Base.metadata.create_all)."""
        try:
            print("🔄 Creating database tables...")
            Base.metadata.create_all(self.engine)
            print("✅ Database tables created successfully")
        except SQLAlchemyError as e:
            print(f"❌ Error creating database: {e}")
            raise

    def check_tables_exist(self) -> bool:
        """
        Inspect the database and verify required tables exist.

        Returns True if both 'ticker_statistics' and 'industry_aggregation' are present.
        """
        inspector = inspect(self.engine)
        required_tables = ['ticker_statistics', 'industry_aggregation']
        existing_tables = inspector.get_table_names()

        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_tables:
            print(f"⚠️  Missing tables: {missing_tables}")
            return False
        return True

    def connect(self):
        """Open an ORM session (Session) for subsequent operations."""
        try:
            self.session = self.Session()
            print("✅ Connected to database successfully")
        except SQLAlchemyError as e:
            print(f"❌ Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close the ORM session if it is open."""
        if self.session:
            self.session.close()
            print("✅ Database connection closed")

    def store_ticker_statistics(self, ticker_data: List[Dict]):
        """
        Insert or update ticker statistics in the database.

        For each record in ticker_data:
          - if an entry with the same (symbol, industry) exists => update fields & last_updated
          - otherwise => create a new TickerStatistics row
        """
        if not self.session:
            self.connect()

        print(f"\n📊 Storing {len(ticker_data)} ticker statistics...")

        stats_count = 0
        for data in ticker_data:
            try:
                # Check if record already exists (same symbol and industry)
                existing = self.session.query(TickerStatistics).filter_by(
                    symbol=data['symbol'],
                    industry=data['industry']
                ).first()

                if existing:
                    # Update existing record with new values
                    existing.pe_ratio = data.get('pe_ratio')
                    existing.revenue_growth = data.get('revenue_growth')
                    existing.net_income_ttm = data.get('net_income_ttm')
                    existing.debt_ratio = data.get('debt_ratio')
                    existing.price = data.get('price', None)
                    existing.revenue_current = data.get('revenue', None)
                    existing.last_updated = datetime.now(timezone.utc)
                    print(f"  🔄 Updated: {data['symbol']}")
                else:
                    # Create new record and add to session
                    ticker = TickerStatistics(
                        symbol=data['symbol'],
                        name=data.get('name', data['symbol']),
                        industry=data['industry'],
                        pe_ratio=data.get('pe_ratio'),
                        revenue_growth=data.get('revenue_growth'),
                        net_income_ttm=data.get('net_income_ttm'),
                        debt_ratio=data.get('debt_ratio'),
                        price=data.get('price', None),
                        revenue_current=data.get('revenue', None),
                        data_date=datetime.now(timezone.utc),
                        is_active=True
                    )
                    self.session.add(ticker)
                    print(f"  ✅ Added: {data['symbol']}")

                stats_count += 1

            except KeyError as e:
                # Defensive: if expected key is missing, log and continue with others
                print(f"  ❌ Missing key in data for {data.get('symbol', 'unknown')}: {e}")
            except SQLAlchemyError as e:
                print(f"  ❌ Database error for {data.get('symbol', 'unknown')}: {e}")

        # Commit changes to the DB in a single transaction
        try:
            self.session.commit()
            print(f"✅ Successfully stored {stats_count} ticker statistics")
            return stats_count
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"❌ Error committing ticker statistics: {e}")
            return 0

    def store_industry_aggregation(self, industry_data: List[Dict]):
        """
        Insert or update industry aggregations.

        For each industry record:
          - if existing by industry name => update fields & last_updated
          - otherwise => create a new IndustryAggregation row
        """
        if not self.session:
            self.connect()

        print(f"\n🏢 Storing {len(industry_data)} industry aggregations...")

        agg_count = 0
        for data in industry_data:
            try:
                existing = self.session.query(IndustryAggregation).filter_by(
                    industry=data['industry']
                ).first()

                if existing:
                    existing.avg_pe_ratio = data.get('avg_pe_ratio')
                    existing.avg_revenue_growth = data.get('avg_revenue_growth')
                    existing.sum_revenue = data.get('sum_revenue')
                    existing.ticker_count = data.get('ticker_count', 0)
                    existing.last_updated = datetime.now(timezone.utc)
                    print(f"  🔄 Updated: {data['industry']}")
                else:
                    industry = IndustryAggregation(
                        industry=data['industry'],
                        avg_pe_ratio=data.get('avg_pe_ratio'),
                        avg_revenue_growth=data.get('avg_revenue_growth'),
                        sum_revenue=data.get('sum_revenue'),
                        ticker_count=data.get('ticker_count', 0),
                        calculation_date=datetime.now(timezone.utc)
                    )
                    self.session.add(industry)
                    print(f"  ✅ Added: {data['industry']}")

                agg_count += 1

            except KeyError as e:
                print(f"  ❌ Missing key in data for {data.get('industry', 'unknown')}: {e}")
            except SQLAlchemyError as e:
                print(f"  ❌ Database error for {data.get('industry', 'unknown')}: {e}")

        try:
            self.session.commit()
            print(f"✅ Successfully stored {agg_count} industry aggregations")
            return agg_count
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"❌ Error committing industry aggregations: {e}")
            return 0

    # ----------------------
    # JSON loading helpers
    # ----------------------
    def load_latest_ticker_statistics(self, data_dir: str = "data") -> List[Dict]:
        """
        Load the newest ticker_statistics_*.json file from the data directory.

        Robustness:
          - First tries `data/` relative to current working directory
          - Then tries `../data/` (when running from src/)
        """
        data_path = Path(data_dir)
        if not data_path.exists():
            # Fallback to parent folder's data/ if current doesn't exist
            data_path = Path("../" + data_dir)

        if not data_path.exists():
            print(f"❌ Data directory not found: {data_dir} (also tried ../{data_dir})")
            return []

        ticker_files = list(data_path.glob("ticker_statistics_*.json"))
        if not ticker_files:
            print("❌ No ticker statistics files found")
            return []

        latest_file = max(ticker_files, key=lambda x: x.stem)
        print(f"📁 Loading ticker data from: {latest_file.name}")

        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            print(f"✅ Loaded {len(data)} ticker records")
            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error loading ticker data: {e}")
            return []

    def load_latest_industry_aggregation(self, data_dir: str = "data") -> List[Dict]:
        """
        Load the newest industry_aggregation_*.json file from the data directory.

        Uses same fallback logic as load_latest_ticker_statistics.
        """
        data_path = Path(data_dir)
        if not data_path.exists():
            data_path = Path("../" + data_dir)

        if not data_path.exists():
            print(f"❌ Data directory not found: {data_dir} (also tried ../{data_dir})")
            return []

        industry_files = list(data_path.glob("industry_aggregation_*.json"))
        if not industry_files:
            print("❌ No industry aggregation files found")
            return []

        latest_file = max(industry_files, key=lambda x: x.stem)
        print(f"📁 Loading industry data from: {latest_file.name}")

        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            print(f"✅ Loaded {len(data)} industry records")
            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error loading industry data: {e}")
            return []

    def display_database_summary(self):
        """Prints a short summary of database contents (counts and some per-row info)."""
        if not self.session:
            self.connect()

        print("\n" + "=" * 80)
        print("DATABASE SUMMARY")
        print("=" * 80)

        try:
            ticker_count = self.session.query(TickerStatistics).count()
            active_tickers = self.session.query(TickerStatistics).filter_by(is_active=True).count()

            print(f"📊 Ticker Statistics:")
            print(f"  • Total records: {ticker_count}")
            print(f"  • Active tickers: {active_tickers}")

            print(f"\n📈 Tickers by Industry:")
            industries = self.session.query(
                TickerStatistics.industry,
                TickerStatistics.is_active
            ).all()

            industry_counts = {}
            active_counts = {}

            for industry, is_active in industries:
                if industry not in industry_counts:
                    industry_counts[industry] = 0
                    active_counts[industry] = 0

                industry_counts[industry] += 1
                if is_active:
                    active_counts[industry] += 1

            for industry in sorted(industry_counts.keys()):
                count = industry_counts[industry]
                active = active_counts.get(industry, 0)
                print(f"  • {industry}: {count} total ({active} active)")

            print(f"\n📋 Detailed Ticker Information:")
            tickers = self.session.query(TickerStatistics).all()
            for ticker in tickers:
                print(f"\n  {ticker.symbol} ({ticker.industry}):")
                if ticker.pe_ratio:
                    print(f"    • PE Ratio: {ticker.pe_ratio:.2f}")
                if ticker.revenue_growth:
                    print(f"    • Revenue Growth: {ticker.revenue_growth:.2f}%")
                if ticker.net_income_ttm:
                    print(f"    • Net Income TTM: ${ticker.net_income_ttm:,.0f}")
                if ticker.debt_ratio:
                    print(f"    • Debt Ratio: {ticker.debt_ratio:.4f}")
                if ticker.price:
                    print(f"    • Price: ${ticker.price:.2f}")
                if ticker.revenue_current:
                    print(f"    • Revenue: ${ticker.revenue_current:,.0f}")

            agg_count = self.session.query(IndustryAggregation).count()

            print(f"\n🏢 Industry Aggregations:")
            print(f"  • Total records: {agg_count}")

            aggregations = self.session.query(IndustryAggregation).all()
            for agg in aggregations:
                print(f"\n  📊 {agg.industry}:")
                print(f"    • Ticker Count: {agg.ticker_count}")
                if agg.avg_pe_ratio is not None:
                    print(f"    • Avg PE Ratio: {agg.avg_pe_ratio:.2f}")
                if agg.avg_revenue_growth is not None:
                    print(f"    • Avg Revenue Growth: {agg.avg_revenue_growth:.2f}%")
                if agg.sum_revenue is not None:
                    print(f"    • Sum Revenue: ${agg.sum_revenue:,.0f}")

        except SQLAlchemyError as e:
            print(f"❌ Error querying database: {e}")

    def backup_database(self, backup_dir: str = "backups"):
        """
        Create a file-copy backup of the SQLite database file.

        Notes:
          - This function detects the actual DB file path using the same heuristic
            used at initialization (self.database_path).
          - Backup folder is created relative to the current working directory.
        """
        import shutil

        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"fiindo_challenge_backup_{timestamp}.db"

        try:
            # Use the resolved database path stored on the instance
            db_file = self.database_path
            if db_file.exists():
                shutil.copy2(db_file, backup_file)
                print(f"✅ Database backed up to: {backup_file.resolve()}")
            else:
                print(f"❌ Database file not found at {db_file.resolve()}")
        except Exception as e:
            print(f"❌ Error creating backup: {e}")


def main():
    """Main orchestration for Step 3: prepare DB, load calculated JSON, store into DB."""
    print("=" * 80)
    print("STEP 3: DATA STORAGE")
    print("=" * 80)

    # Initialize DataStorage. This will resolve the database path and create the engine.
    storage = DataStorage()

    try:
        # ---------------------------
        # 1) Database existence & tables
        # ---------------------------
        print("\n🔧 DATABASE SETUP")
        print("-" * 40)

        # We use the resolved path stored on the storage instance to decide if DB exists.
        db_file_path = storage.database_path

        # If the DB file doesn't exist yet (first run), create tables.
        if not db_file_path.exists():
            print(f"📁 Creating new database at {db_file_path}")
            storage.create_database()
        else:
            print(f"📁 Database file already exists at {db_file_path}")

            # Verify required tables exist; create them if missing.
            if not storage.check_tables_exist():
                print("⚠️  Creating missing tables...")
                storage.create_database()
            else:
                print("✅ All tables exist")

        # ---------------------------
        # 2) Load JSON outputs from Step 2
        # ---------------------------
        print("\n📥 LOADING CALCULATED DATA")
        print("-" * 40)

        # These methods use a fallback to ../data/ if data/ is not present (robust for src/ execution)
        ticker_data = storage.load_latest_ticker_statistics()
        industry_data = storage.load_latest_industry_aggregation()

        if not ticker_data and not industry_data:
            print("❌ No data to store. Please run Step 2 first.")
            return

        # ---------------------------
        # 3) Connect to DB & write data
        # ---------------------------
        storage.connect()

        # Store ticker stats
        if ticker_data:
            ticker_count = storage.store_ticker_statistics(ticker_data)
            if ticker_count == 0:
                print("⚠️  No ticker statistics were stored")
        else:
            print("⚠️  No ticker data to store")

        # Store industry aggregations
        if industry_data:
            industry_count = storage.store_industry_aggregation(industry_data)
            if industry_count == 0:
                print("⚠️  No industry aggregations were stored")
        else:
            print("⚠️  No industry data to store")

        # Display DB summary
        storage.display_database_summary()

        # ---------------------------
        # 4) Optional backup
        # ---------------------------
        print("\n💾 DATABASE BACKUP")
        print("-" * 40)
        backup_choice = input("Create database backup? (y/N): ").strip().lower()
        if backup_choice == 'y':
            storage.backup_database()
        else:
            print("Skipping backup")

        # Final summary and helpful hints for inspection
        print("\n" + "=" * 80)
        print("✅ STEP 3 COMPLETED!")
        print("=" * 80)

        print(f"\n📋 DATA STORAGE SUMMARY:")
        print(f"  • Database: {storage.database_path}")
        print(f"  • Ticker statistics considered: {len(ticker_data) if ticker_data else 0}")
        print(f"  • Industry aggregations considered: {len(industry_data) if industry_data else 0}")

        print(f"\n📁 DATABASE TABLES:")
        print(f"  1. ticker_statistics - Individual ticker data")
        print(f"  2. industry_aggregation - Aggregated industry data")

        print(f"\n🔍 You can inspect the database directly with:")
        print(f"    sqlite3 {storage.database_path}")
        print(f"    .tables                    # Show all tables")
        print(f"    SELECT * FROM ticker_statistics LIMIT 5;")
        print(f"    SELECT * FROM industry_aggregation;")

        print(f"\n➡️  NEXT: The data is now ready for analysis and reporting.")

    except Exception as e:
        # Print an informative error and full traceback (helps debugging file-permission/path issues)
        print(f"\n❌ Error in Step 3: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Ensure we close the DB session cleanly
        storage.disconnect()


if __name__ == "__main__":
    main()
