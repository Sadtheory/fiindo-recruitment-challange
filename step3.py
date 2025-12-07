# step3_data_storage.py

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import der Datenbank-Modelle
sys.path.append('src')  # Füge src-Verzeichnis zum Python-Pfad hinzu
try:
    from models import Base, TickerStatistics, IndustryAggregation

    print("✅ Database models imported successfully")
except ImportError as e:
    print(f"❌ Error importing database models: {e}")
    print("Please ensure models.py is in the src/ directory")
    sys.exit(1)


class DataStorage:
    """Klasse für das Speichern der berechneten Daten in der Datenbank"""

    def __init__(self, database_url: str = "sqlite:///fiindo_challenge.db"):
        """Initialisiert die Datenbankverbindung"""
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.session = None

    def create_database(self):
        """Erstellt die Datenbank-Tabellen"""
        try:
            print("🔄 Creating database tables...")
            Base.metadata.create_all(self.engine)
            print("✅ Database tables created successfully")
        except SQLAlchemyError as e:
            print(f"❌ Error creating database: {e}")
            raise

    def check_tables_exist(self) -> bool:
        """Überprüft, ob die Tabellen existieren"""
        inspector = inspect(self.engine)
        required_tables = ['ticker_statistics', 'industry_aggregation']
        existing_tables = inspector.get_table_names()

        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_tables:
            print(f"⚠️  Missing tables: {missing_tables}")
            return False
        return True

    def connect(self):
        """Stellt eine Datenbankverbindung her"""
        try:
            self.session = self.Session()
            print("✅ Connected to database successfully")
        except SQLAlchemyError as e:
            print(f"❌ Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Schließt die Datenbankverbindung"""
        if self.session:
            self.session.close()
            print("✅ Database connection closed")

    def store_ticker_statistics(self, ticker_data: List[Dict]):
        """Speichert Ticker-Statistiken in der Datenbank"""
        if not self.session:
            self.connect()

        print(f"\n📊 Storing {len(ticker_data)} ticker statistics...")

        stats_count = 0
        for data in ticker_data:
            try:
                # Überprüfe ob der Eintrag bereits existiert
                existing = self.session.query(TickerStatistics).filter_by(
                    symbol=data['symbol'],
                    industry=data['industry']
                ).first()

                if existing:
                    # Aktualisiere bestehenden Eintrag
                    existing.pe_ratio = data.get('pe_ratio')
                    existing.revenue_growth = data.get('revenue_growth')
                    existing.net_income_ttm = data.get('net_income_ttm')
                    existing.debt_ratio = data.get('debt_ratio')
                    existing.price = data.get('price', None)
                    existing.revenue_current = data.get('revenue', None)
                    existing.last_updated = datetime.now(timezone.utc)
                    print(f"  🔄 Updated: {data['symbol']}")
                else:
                    # Erstelle neuen Eintrag
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
                print(f"  ❌ Missing key in data for {data.get('symbol', 'unknown')}: {e}")
            except SQLAlchemyError as e:
                print(f"  ❌ Database error for {data.get('symbol', 'unknown')}: {e}")

        try:
            self.session.commit()
            print(f"✅ Successfully stored {stats_count} ticker statistics")
            return stats_count
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"❌ Error committing ticker statistics: {e}")
            return 0

    def store_industry_aggregation(self, industry_data: List[Dict]):
        """Speichert Industrie-Aggregationen in der Datenbank"""
        if not self.session:
            self.connect()

        print(f"\n🏢 Storing {len(industry_data)} industry aggregations...")

        agg_count = 0
        for data in industry_data:
            try:
                # Überprüfe ob der Eintrag bereits existiert
                existing = self.session.query(IndustryAggregation).filter_by(
                    industry=data['industry']
                ).first()

                if existing:
                    # Aktualisiere bestehenden Eintrag
                    existing.avg_pe_ratio = data.get('avg_pe_ratio')
                    existing.avg_revenue_growth = data.get('avg_revenue_growth')
                    existing.sum_revenue = data.get('sum_revenue')
                    existing.ticker_count = data.get('ticker_count', 0)
                    existing.last_updated = datetime.now(timezone.utc)
                    print(f"  🔄 Updated: {data['industry']}")
                else:
                    # Erstelle neuen Eintrag
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

    def load_latest_ticker_statistics(self, data_dir: str = "data") -> List[Dict]:
        """Lädt die neuesten Ticker-Statistiken aus JSON-Dateien"""
        data_path = Path(data_dir)

        if not data_path.exists():
            print(f"❌ Data directory not found: {data_dir}")
            return []

        # Finde alle ticker_statistics JSON Dateien
        ticker_files = list(data_path.glob("ticker_statistics_*.json"))

        if not ticker_files:
            print("❌ No ticker statistics files found")
            return []

        # Nimm die neueste Datei (basierend auf Timestamp im Dateinamen)
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
        """Lädt die neuesten Industrie-Aggregationen aus JSON-Dateien"""
        data_path = Path(data_dir)

        if not data_path.exists():
            print(f"❌ Data directory not found: {data_dir}")
            return []

        # Finde alle industry_aggregation JSON Dateien
        industry_files = list(data_path.glob("industry_aggregation_*.json"))

        if not industry_files:
            print("❌ No industry aggregation files found")
            return []

        # Nimm die neueste Datei (basierend auf Timestamp im Dateinamen)
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
        """Zeigt eine Zusammenfassung der Datenbankinhalte"""
        if not self.session:
            self.connect()

        print("\n" + "=" * 80)
        print("DATABASE SUMMARY")
        print("=" * 80)

        try:
            # Zähle Ticker-Statistiken
            ticker_count = self.session.query(TickerStatistics).count()
            active_tickers = self.session.query(TickerStatistics).filter_by(is_active=True).count()

            print(f"📊 Ticker Statistics:")
            print(f"  • Total records: {ticker_count}")
            print(f"  • Active tickers: {active_tickers}")

            # Zeige Ticker nach Industrie
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

            # Zeige detaillierte Ticker-Informationen
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

            # Zähle Industrie-Aggregationen
            agg_count = self.session.query(IndustryAggregation).count()

            print(f"\n🏢 Industry Aggregations:")
            print(f"  • Total records: {agg_count}")

            # Zeige alle Aggregationen
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
        """Erstellt ein Backup der Datenbank"""
        import shutil
        from datetime import datetime

        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"fiindo_challenge_backup_{timestamp}.db"

        try:
            # Für SQLite: Kopiere die Datenbankdatei
            if "sqlite" in self.database_url:
                db_file = Path("fiindo_challenge.db")
                if db_file.exists():
                    shutil.copy2(db_file, backup_file)
                    print(f"✅ Database backed up to: {backup_file}")
                else:
                    print("❌ Database file not found")
            else:
                print("⚠️  Backup currently only supported for SQLite databases")

        except Exception as e:
            print(f"❌ Error creating backup: {e}")


def main():
    """Hauptfunktion für Data Storage"""
    print("=" * 80)
    print("STEP 3: DATA STORAGE")
    print("=" * 80)

    # Datenbank-Initialisierung
    storage = DataStorage()

    try:
        # 1. Datenbank erstellen/überprüfen
        print("\n🔧 DATABASE SETUP")
        print("-" * 40)

        if not Path("fiindo_challenge.db").exists():
            print("📁 Creating new database...")
            storage.create_database()
        else:
            print("📁 Database file already exists")

            # Überprüfe ob Tabellen existieren
            if not storage.check_tables_exist():
                print("⚠️  Creating missing tables...")
                storage.create_database()
            else:
                print("✅ All tables exist")

        # 2. Daten laden
        print("\n📥 LOADING CALCULATED DATA")
        print("-" * 40)

        ticker_data = storage.load_latest_ticker_statistics()
        industry_data = storage.load_latest_industry_aggregation()

        if not ticker_data and not industry_data:
            print("❌ No data to store. Please run Step 2 first.")
            return

        # 3. Verbindung zur Datenbank herstellen
        storage.connect()

        # 4. Ticker-Statistiken speichern
        if ticker_data:
            ticker_count = storage.store_ticker_statistics(ticker_data)
            if ticker_count == 0:
                print("⚠️  No ticker statistics were stored")
        else:
            print("⚠️  No ticker data to store")

        # 5. Industrie-Aggregationen speichern
        if industry_data:
            industry_count = storage.store_industry_aggregation(industry_data)
            if industry_count == 0:
                print("⚠️  No industry aggregations were stored")
        else:
            print("⚠️  No industry data to store")

        # 6. Datenbank-Zusammenfassung anzeigen
        storage.display_database_summary()

        # 7. Backup erstellen (optional)
        print("\n💾 DATABASE BACKUP")
        print("-" * 40)
        backup_choice = input("Create database backup? (y/N): ").strip().lower()
        if backup_choice == 'y':
            storage.backup_database()
        else:
            print("Skipping backup")

        print("\n" + "=" * 80)
        print("✅ STEP 3 COMPLETED!")
        print("=" * 80)

        print(f"\n📋 DATA STORAGE SUMMARY:")
        print(f"  • Database: fiindo_challenge.db")
        print(f"  • Ticker statistics stored: {len(ticker_data) if ticker_data else 0}")
        print(f"  • Industry aggregations stored: {len(industry_data) if industry_data else 0}")

        print(f"\n📁 DATABASE TABLES:")
        print(f"  1. ticker_statistics - Individual ticker data")
        print(f"  2. industry_aggregation - Aggregated industry data")

        print(f"\n🔍 You can inspect the database using:")
        print(f"    sqlite3 fiindo_challenge.db")
        print(f"    .tables                    # Show all tables")
        print(f"    SELECT * FROM ticker_statistics LIMIT 5;")
        print(f"    SELECT * FROM industry_aggregation;")

        print(f"\n📊 INTERESTING QUERIES:")
        print(f"    -- Get all tickers with PE Ratio")
        print(f"    SELECT symbol, industry, pe_ratio FROM ticker_statistics WHERE pe_ratio IS NOT NULL;")
        print(f"")
        print(f"    -- Get industry averages")
        print(f"    SELECT industry, avg_pe_ratio, avg_revenue_growth FROM industry_aggregation;")
        print(f"")
        print(f"    -- Count tickers by industry")
        print(f"    SELECT industry, COUNT(*) as ticker_count FROM ticker_statistics GROUP BY industry;")

        print(f"\n➡️  NEXT: The data is now ready for analysis and reporting.")

    except Exception as e:
        print(f"\n❌ Error in Step 3: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 8. Verbindung schließen
        storage.disconnect()


if __name__ == "__main__":
    main()