# run_tests.py (liegt in tests/)
import sys
import os
import subprocess
from pathlib import Path

# Bestimme das Projekt-Root (eine Ebene über tests/)
project_root = Path(__file__).parent.parent
os.chdir(project_root)

print(f"📁 Project root: {project_root}")
print(f"📁 Current directory: {os.getcwd()}")

# Liste aller Testdateien (relativ zum Projekt-Root)
test_files = [
    "tests/test_step1_fetch.py",
    "tests/test_step2_transform.py",
    "tests/test_step3_load.py"
]

# Überprüfe ob die Dateien existieren
print("\n🔍 Checking test files...")
for test_file in test_files:
    full_path = project_root / test_file
    if full_path.exists():
        print(f"  ✅ {test_file} exists")
    else:
        print(f"  ❌ {test_file} not found at {full_path}")

print("\n🧪 Running all tests...\n")

all_passed = True

for test_file in test_files:
    full_path = project_root / test_file

    if not full_path.exists():
        print(f"\n{'=' * 60}")
        print(f"❌ Test file not found: {test_file}")
        print(f"   Expected at: {full_path}")
        print('=' * 60)
        all_passed = False
        continue

    print(f"\n{'=' * 60}")
    print(f"Testing: {test_file}")
    print('=' * 60)

    try:
        # Führe Testdatei mit pytest aus
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(full_path), "-v"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Gib die Ausgabe aus
        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            print(f"✅ {test_file}: All tests passed!\n")
        else:
            print(f"❌ {test_file}: Some tests failed (return code: {result.returncode})")
            if result.stderr:
                print("Stderr output:", result.stderr[:500])  # Nur ersten 500 Zeichen
            all_passed = False

    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file}: Tests timed out after 30 seconds")
        all_passed = False
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        all_passed = False

print(f"\n{'=' * 60}")
if all_passed:
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
else:
    print("⚠️  SOME TESTS FAILED")
print('=' * 60)

# Exit mit entsprechendem Code
sys.exit(0 if all_passed else 1)