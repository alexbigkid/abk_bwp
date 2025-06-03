"""Tests for db.py."""

import unittest
from unittest import mock

# Re-import your context manager
from abk_bwp.db import db_sqlite_connect, db_sqlite_cursor


class TestDbSqliteConnect(unittest.TestCase):
    """TestDbSqliteConnect class."""

    @mock.patch("abk_bwp.db.sqlite3.connect")
    def test_db_sqlite_connect_opens_and_closes(self, mock_connect):
        """Test test_db_sqlite_connect_opens_and_closes."""
        # Arrange
        # ----------------------------------
        # Mock connection object
        mock_conn = mock.MagicMock()
        mock_connect.return_value = mock_conn
        db_file_name = "fake.db"

        # Act
        # ----------------------------------
        with db_sqlite_connect(db_file_name) as conn:
            # Inside context, conn should be the mock
            self.assertEqual(conn, mock_conn)
            self.assertFalse(conn.autocommit)

        # Assert: connection was opened and closed
        # ----------------------------------
        mock_connect.assert_called_once_with(db_file_name)
        mock_conn.close.assert_called_once()


class TestDbSqliteCursor(unittest.TestCase):
    """TestDbSqliteCursor class."""

    def test_db_sqlite_cursor_opens_and_closes_cursor(self):
        """Test test_db_sqlite_cursor_opens_and_closes_cursor."""
        # Arrange
        # ----------------------------------
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Act
        # ----------------------------------
        with db_sqlite_cursor(mock_conn) as cursor:
            # Inside the context: cursor should be the mocked one
            self.assertEqual(cursor, mock_cursor)

        # Assert: cursor() was called and closed
        # ----------------------------------
        mock_conn.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
