# run_tests.py
import sys
import os
import subprocess

# Stelle sicher dass wir im richtigen Verzeichnis sind
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Liste aller Testdateien
test_files = [
    "tests/test_step1_fetch.py",
    "tests/test_step2_transform.py",
    "tests/test_step3_load.py"
]

print("🧪 Running all tests...\n")

all_passed = True

for test_file in test_files:
    print(f"\n{'=' * 60}")
    print(f"Testing: {test_file}")
    print('=' * 60)

    try:
        # Führe Testdatei direkt aus
        result = subprocess.run([sys.executable, test_file],
                                capture_output=True,
                                text=True)

        if result.returncode == 0:
            print("✅ All tests passed!\n")
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            if result.stderr:
                print("Stderr:", result.stderr)
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