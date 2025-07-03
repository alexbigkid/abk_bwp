"""Populates initial values of DB."""

import sqlite3
import csv

from abk_bwp.db import DB_BWP_FILE_NAME, DB_BWP_TABLE, DBColumns


DB_CSV_FILE = "db.csv"


def main(verbose: bool = True):
    """Main function to create initial values.

    Args:
        verbose: If True, print insertion statistics
    """
    conn = None
    rows = []
    try:
        # Connect to SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect(DB_BWP_FILE_NAME)
        cur = conn.cursor()

        # Read CSV and extract headers and rows
        with open(DB_CSV_FILE, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames
            if fieldnames is None:
                raise ValueError("CSV file is empty or missing headers")

            # Build CREATE TABLE statement dynamically
            create_columns = []
            for name in fieldnames:
                if name == DBColumns.PAGE_ID.value:
                    create_columns.append(f"{name} INTEGER PRIMARY KEY")
                else:
                    create_columns.append(f"{name} TEXT NOT NULL")
            create_stmt = f"""
                CREATE TABLE IF NOT EXISTS {DB_BWP_TABLE} (
                    {", ".join(create_columns)}
                )
            """
            cur.execute(create_stmt)

            # Prepare rows
            for row in reader:
                values = [
                    int(row[name]) if name == DBColumns.PAGE_ID.value else row[name]
                    for name in fieldnames
                ]
                rows.append(tuple(values))

        # Use INSERT OR IGNORE to avoid duplicates based on pageId
        placeholders = ", ".join(["?"] * len(fieldnames))
        insert_stmt = f"""
            INSERT OR IGNORE INTO {DB_BWP_TABLE} ({", ".join(fieldnames)})
            VALUES ({placeholders})
        """  # noqa: S608
        cur.executemany(insert_stmt, rows)

        # Commit changes
        conn.commit()
    finally:
        if conn:
            conn.close()

    if verbose:
        print(f"Inserted {len(rows)} rows into the '{DB_BWP_TABLE}' table.")


if __name__ == "__main__":
    main()
