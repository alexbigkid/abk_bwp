"""Unit tests for populate_db.py."""

import sqlite3
import unittest
from unittest import mock
from unittest.mock import mock_open, patch, MagicMock

from abk_bwp import populate_db


class TestPopulateDbMain(unittest.TestCase):
    """TestPopulateDbMain class."""

    def setUp(self):
        """Set up tests for populate_db."""
        self.maxDiff = None

    # -------------------------------------------------------------------------
    # Test successful database population
    # -------------------------------------------------------------------------
    @patch("builtins.open", new_callable=mock_open)
    @patch("sqlite3.connect")
    @patch("csv.DictReader")
    def test_main_successful_population(self, mock_csv_reader, mock_connect, mock_file):
        """Test successful database population from CSV."""
        # Arrange - Mock CSV data
        mock_csv_data = [
            {"pageId": "12345", "country": "US", "date": "2024-01-01", "pageUrl": "http://example.com/1"},
            {"pageId": "12346", "country": "UK", "date": "2024-01-02", "pageUrl": "http://example.com/2"},
        ]
        mock_reader_instance = MagicMock()
        mock_reader_instance.fieldnames = ["pageId", "country", "date", "pageUrl"]
        mock_reader_instance.__iter__ = lambda self: iter(mock_csv_data)
        mock_csv_reader.return_value = mock_reader_instance

        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Act
        with patch("builtins.print") as mock_print:
            populate_db.main()

        # Assert - Database operations
        mock_connect.assert_called_once_with(populate_db.DB_BWP_FILE_NAME)
        mock_conn.cursor.assert_called_once()

        # Verify CREATE TABLE was called
        create_table_calls = [call for call in mock_cursor.execute.call_args_list if "CREATE TABLE" in str(call)]
        self.assertEqual(len(create_table_calls), 1)
        create_table_sql = create_table_calls[0][0][0]
        self.assertIn("CREATE TABLE IF NOT EXISTS", create_table_sql)
        self.assertIn("pageId INTEGER PRIMARY KEY", create_table_sql)
        self.assertIn("country TEXT NOT NULL", create_table_sql)

        # Verify INSERT statements
        expected_rows = [(12345, "US", "2024-01-01", "http://example.com/1"), (12346, "UK", "2024-01-02", "http://example.com/2")]
        mock_cursor.executemany.assert_called_once()
        executemany_call = mock_cursor.executemany.call_args
        self.assertIn("INSERT OR IGNORE INTO", executemany_call[0][0])
        self.assertEqual(executemany_call[0][1], expected_rows)

        # Verify commit and close
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify print statement
        mock_print.assert_called_once_with("Inserted 2 rows into the 'pages' table.")

    # -------------------------------------------------------------------------
    # Test empty CSV file handling
    # -------------------------------------------------------------------------
    @patch("builtins.open", new_callable=mock_open)
    @patch("sqlite3.connect")
    @patch("csv.DictReader")
    def test_main_empty_csv_file(self, mock_csv_reader, mock_connect, mock_file):
        """Test handling of empty CSV file."""
        # Arrange - Mock empty CSV
        mock_reader_instance = MagicMock()
        mock_reader_instance.fieldnames = None
        mock_csv_reader.return_value = mock_reader_instance

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            populate_db.main(verbose=False)

        self.assertEqual(str(context.exception), "CSV file is empty or missing headers")
        mock_conn.close.assert_called_once()

    # -------------------------------------------------------------------------
    # Test CSV file with no data rows
    # -------------------------------------------------------------------------
    @patch("builtins.open", new_callable=mock_open)
    @patch("sqlite3.connect")
    @patch("csv.DictReader")
    def test_main_csv_headers_only(self, mock_csv_reader, mock_connect, mock_file):
        """Test CSV file with headers but no data rows."""
        # Arrange - Mock CSV with headers but no data
        mock_reader_instance = MagicMock()
        mock_reader_instance.fieldnames = ["pageId", "country", "date", "pageUrl"]
        mock_reader_instance.__iter__ = lambda self: iter([])  # No data rows
        mock_csv_reader.return_value = mock_reader_instance

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Act
        with patch("builtins.print") as mock_print:
            populate_db.main()  # Use default verbose=True to test print statement

        # Assert
        mock_cursor.execute.assert_called_once()  # CREATE TABLE only
        mock_cursor.executemany.assert_called_once_with(mock.ANY, [])  # Empty list
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        mock_print.assert_called_once_with("Inserted 0 rows into the 'pages' table.")

    # -------------------------------------------------------------------------
    # Test database connection failure
    # -------------------------------------------------------------------------
    @patch("sqlite3.connect")
    def test_main_database_connection_failure(self, mock_connect):
        """Test handling of database connection failure."""
        # Arrange
        mock_connect.side_effect = sqlite3.Error("Connection failed")

        # Act & Assert
        with self.assertRaises(sqlite3.Error):
            populate_db.main(verbose=False)

    # -------------------------------------------------------------------------
    # Test CSV file reading failure
    # -------------------------------------------------------------------------
    @patch("builtins.open", side_effect=FileNotFoundError("CSV file not found"))
    @patch("sqlite3.connect")
    def test_main_csv_file_not_found(self, mock_connect, mock_file):
        """Test handling of missing CSV file."""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            populate_db.main(verbose=False)

        # Verify connection is still closed in finally block
        mock_conn.close.assert_called_once()

    # -------------------------------------------------------------------------
    # Test different field configurations
    # -------------------------------------------------------------------------
    @patch("builtins.open", new_callable=mock_open)
    @patch("sqlite3.connect")
    @patch("csv.DictReader")
    def test_main_handles_different_field_types(self, mock_csv_reader, mock_connect, mock_file):
        """Test handling of different field configurations."""
        # Arrange - CSV with different column order
        mock_csv_data = [{"country": "CA", "pageId": "98765", "pageUrl": "http://example.ca", "date": "2024-03-01"}]
        mock_reader_instance = MagicMock()
        mock_reader_instance.fieldnames = ["country", "pageId", "pageUrl", "date"]  # Different order
        mock_reader_instance.__iter__ = lambda self: iter(mock_csv_data)
        mock_csv_reader.return_value = mock_reader_instance

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Act
        populate_db.main(verbose=False)

        # Assert - Verify CREATE TABLE handles pageId as PRIMARY KEY
        create_table_call = mock_cursor.execute.call_args_list[0]
        create_table_sql = create_table_call[0][0]
        self.assertIn("pageId INTEGER PRIMARY KEY", create_table_sql)
        self.assertIn("country TEXT NOT NULL", create_table_sql)

        # Verify data insertion with correct type conversion
        expected_rows = [("CA", 98765, "http://example.ca", "2024-03-01")]
        executemany_call = mock_cursor.executemany.call_args
        self.assertEqual(executemany_call[0][1], expected_rows)

    # -------------------------------------------------------------------------
    # Test pageId integer conversion
    # -------------------------------------------------------------------------
    @patch("builtins.open", new_callable=mock_open)
    @patch("sqlite3.connect")
    @patch("csv.DictReader")
    def test_main_converts_page_id_to_integer(self, mock_csv_reader, mock_connect, mock_file):
        """Test that pageId is properly converted to integer."""
        # Arrange
        mock_csv_data = [{"pageId": "54321", "country": "DE", "date": "2024-02-15", "pageUrl": "http://example.de"}]
        mock_reader_instance = MagicMock()
        mock_reader_instance.fieldnames = ["pageId", "country", "date", "pageUrl"]
        mock_reader_instance.__iter__ = lambda self: iter(mock_csv_data)
        mock_csv_reader.return_value = mock_reader_instance

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Act
        populate_db.main(verbose=False)

        # Assert - pageId should be converted to int, others remain strings
        expected_rows = [(54321, "DE", "2024-02-15", "http://example.de")]
        executemany_call = mock_cursor.executemany.call_args
        self.assertEqual(executemany_call[0][1], expected_rows)

        # Verify the first element is indeed an integer
        actual_page_id = executemany_call[0][1][0][0]
        self.assertIsInstance(actual_page_id, int)
        self.assertEqual(actual_page_id, 54321)

    # -------------------------------------------------------------------------
    # Test SQL injection protection
    # -------------------------------------------------------------------------
    @patch("builtins.open", new_callable=mock_open)
    @patch("sqlite3.connect")
    @patch("csv.DictReader")
    def test_main_uses_parameterized_queries(self, mock_csv_reader, mock_connect, mock_file):
        """Test that the function uses parameterized queries for SQL injection protection."""
        # Arrange
        mock_csv_data = [
            {"pageId": "1", "country": "'; DROP TABLE pages; --", "date": "2024-01-01", "pageUrl": "http://evil.com"}
        ]
        mock_reader_instance = MagicMock()
        mock_reader_instance.fieldnames = ["pageId", "country", "date", "pageUrl"]
        mock_reader_instance.__iter__ = lambda self: iter(mock_csv_data)
        mock_csv_reader.return_value = mock_reader_instance

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Act
        populate_db.main(verbose=False)

        # Assert - Verify executemany is used with parameterized query
        executemany_call = mock_cursor.executemany.call_args
        sql_statement = executemany_call[0][0]

        # Should use placeholders, not direct string interpolation for values
        self.assertIn("VALUES (?, ?, ?, ?)", sql_statement)

        # Data should be passed as separate parameter
        expected_rows = [(1, "'; DROP TABLE pages; --", "2024-01-01", "http://evil.com")]
        self.assertEqual(executemany_call[0][1], expected_rows)


class TestPopulateDbConstants(unittest.TestCase):
    """Test constants and imports in populate_db module."""

    def test_db_csv_file_constant(self):
        """Test that DB_CSV_FILE constant is properly defined."""
        self.assertEqual(populate_db.DB_CSV_FILE, "db.csv")

    def test_imports_from_db_module(self):
        """Test that required imports from db module are available."""
        # Verify the module has access to required DB constants
        self.assertTrue(hasattr(populate_db, "DB_BWP_FILE_NAME"))
        self.assertTrue(hasattr(populate_db, "DB_BWP_TABLE"))
        self.assertTrue(hasattr(populate_db, "DBColumns"))


if __name__ == "__main__":
    unittest.main()
