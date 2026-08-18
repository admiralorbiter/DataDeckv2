import argparse
import sys
from pathlib import Path

# Add project root directory to sys.path so app and models can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from routes.admin import import_districts_and_schools


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import districts and schools from a CSV file into the database."
    )
    parser.add_argument(
        "csv_path",
        type=str,
        help="Path to the CSV file containing district and school data.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the import process without writing changes to the database.",
    )
    return parser.parse_args()


def import_schools_and_districts_cli(csv_path: str, dry_run: bool = False):
    path = Path(csv_path)
    if not path.is_file():
        print(f"Error: File not found at '{csv_path}'")
        sys.exit(1)

    app = create_app()

    with app.app_context():
        result = import_districts_and_schools(path, dry_run=dry_run)

        for err in result["errors"]:
            print(f"[ERROR] {err}")

        print("\n" + "=" * 50)
        if dry_run:
            print("         SUMMARY (DRY RUN - NO CHANGES SAVED)     ")
        else:
            print("                IMPORT SUMMARY                    ")
        print("=" * 50)
        print(f"  Districts Created  : {result['districts_created']}")
        print(f"  Districts Reused   : {result['districts_reused']}")
        print(f"  Schools Created    : {result['schools_created']}")
        print(f"  Schools Skipped    : {result['schools_skipped']}")
        print(f"  Row Errors         : {result['error_rows']}")
        print("=" * 50)


if __name__ == "__main__":
    args = parse_args()
    import_schools_and_districts_cli(args.csv_path, dry_run=args.dry_run)
