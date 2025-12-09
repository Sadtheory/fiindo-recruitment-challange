# run_pipeline.py
import subprocess
import sys
import os
import argparse

parser = argparse.ArgumentParser(
    prog='fiindo_etl_pipeline',
    description='What the program does',
    epilog='Text at the bottom of help')

parser.add_argument('--starting_at')
args = parser.parse_args()


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
    steps = [
        lambda: run_command("docker-compose run --rm step1-fetch",
                            "Step 1: Fetching data from Fiindo API"),
        lambda: run_command("docker-compose run --rm step2-transform",
                            "Step 2: Transforming data"),
        lambda: run_command("docker-compose run --rm step3-load",
                            "Step 3: Loading data to database"),
        lambda: run_command("docker-compose run --rm check-db",
                            "Step 4: Checking database content")
    ]

    print("🚀 Starting Fiindo Data Pipeline")
    print("=" * 50)

    step_index = 0
    if args.starting_at is not None and args.starting_at.startswith("step"):
        step_index = int(args.starting_at[4]) - 1

    for index in range(step_index, 4):
        if not steps[index]():
            sys.exit(index + 1)

    print("\n" + "=" * 50)
    print("🎉 Pipeline completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()