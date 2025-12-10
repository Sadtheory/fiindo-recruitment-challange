# run_pipeline.py
import subprocess
import sys
import os
import argparse

# Create argument parser for handling command line arguments
parser = argparse.ArgumentParser(
    prog='fiindo_etl_pipeline',  # Name of the program
    description='What the program does',  # Description shown in help
    epilog='Text at the bottom of help')  # Footer text in help

# Add argument to specify which step to start at
parser.add_argument('--starting_at')
# Parse command line arguments
args = parser.parse_args()


def run_command(command, description):
    """Run a command and check its exit code."""
    print(f"\n{'=' * 50}")
    print(f"{description}")
    print(f"{'=' * 50}")

    try:
        # Execute the shell command
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        # Handle command failure
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """
    Main function to orchestrate the ETL pipeline.
    Defines the sequence of steps and executes them in order.
    Supports starting from a specific step using command line argument.
    """

    # Define the pipeline steps as lambda functions
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

    # Determine which step to start from based on command line argument
    step_index = 0
    if args.starting_at is not None and args.starting_at.startswith("step"):
        # Extract step number from argument (e.g., "step2" -> index 1)
        step_index = int(args.starting_at[4]) - 1

    # Execute steps starting from the specified index
    for index in range(step_index, 4):
        if not steps[index]():
            # Exit with step number as exit code if step fails
            sys.exit(index + 1)

    print("\n" + "=" * 50)
    print("🎉 Pipeline completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()