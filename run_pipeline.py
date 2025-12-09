# run_pipeline.py
import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and check its exit code."""
    print(f"\n{'=' * 50}")
    print(f"{description}")
    print(f"{'=' * 50}")

    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    print("🚀 Starting Fiindo Data Pipeline")
    print("=" * 50)

    # Step 1: Fetch data
    if not run_command("docker-compose run --rm fetcher",
                       "Step 1: Fetching data from Fiindo API"):
        sys.exit(1)

    # Step 2: Transform data
    if not run_command("docker-compose run --rm transformer",
                       "Step 2: Transforming data"):
        sys.exit(1)

    # Step 3: Load to database
    if not run_command("docker-compose run --rm loader",
                       "Step 3: Loading data to database"):
        sys.exit(1)

    # Check database
    run_command("docker-compose run --rm check-db",
                "Step 4: Checking database content")

    print("\n" + "=" * 50)
    print("🎉 Pipeline completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()