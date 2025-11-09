"""
Database Management Module

This module handles all SQLite database operations including:
- Article storage and retrieval
- Duplicate detection
- Monitoring logs
- Database maintenance and cleanup
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager for article tracking and monitoring logs.

    Attributes:
        db_path (Path): Path to the SQLite database file
    """

    def __init__(self, db_path: str = "data/articles.db"):
        """
        Initialize database connection and create tables if needed.

        Args:
            db_path: Path to SQLite database file

        Raises:
            sqlite3.Error: If database initialization fails
        """
        self.db_path = Path(db_path)

        # Create data directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            >>> with db._get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM articles")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """
        Create database tables if they don't exist.

        Tables:
            - articles: Stores article information and notification status
            - monitoring_logs: Stores monitoring run history and statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    published_date DATETIME,
                    matched_keyword TEXT NOT NULL,
                    full_content TEXT,
                    notified BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on article_id for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_article_id
                ON articles(article_id)
            """)

            # Create index on notified status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notified
                ON articles(notified)
            """)

            # Create monitoring logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    articles_found INTEGER DEFAULT 0,
                    new_articles INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    execution_time_seconds REAL
                )
            """)

            # Create index on check_time
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_check_time
                ON monitoring_logs(check_time)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def article_exists(self, article_id: str) -> bool:
        """
        Check if an article already exists in the database.

        Args:
            article_id: Unique identifier for the article

        Returns:
            bool: True if article exists, False otherwise

        Example:
            >>> if not db.article_exists("article-123"):
            ...     db.add_article(article_data)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM articles WHERE article_id = ?",
                (article_id,)
            )
            return cursor.fetchone() is not None

    def add_article(self, article_data: Dict[str, Any]) -> bool:
        """
        Add a new article to the database.

        Args:
            article_data: Dictionary containing article information
                Required keys: article_id, title, url, matched_keyword
                Optional keys: published_date, full_content

        Returns:
            bool: True if article was added, False if it already exists

        Example:
            >>> article = {
            ...     'article_id': 'article-123',
            ...     'title': 'New product release',
            ...     'url': 'https://example.com/article-123',
            ...     'matched_keyword': 'バンドー化学',
            ...     'full_content': 'Article content here...'
            ... }
            >>> db.add_article(article)
            True
        """
        if self.article_exists(article_data['article_id']):
            logger.debug(f"Article already exists: {article_data['article_id']}")
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO articles (
                        article_id, title, url, published_date,
                        matched_keyword, full_content, notified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_data['article_id'],
                    article_data['title'],
                    article_data['url'],
                    article_data.get('published_date'),
                    article_data['matched_keyword'],
                    article_data.get('full_content', ''),
                    False
                ))
                logger.info(f"Added new article: {article_data['title']}")
                return True

        except sqlite3.IntegrityError as e:
            logger.warning(f"Article already exists (race condition): {article_data['article_id']}")
            return False
        except Exception as e:
            logger.error(f"Failed to add article: {e}")
            raise

    def get_unnotified_articles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve articles that haven't been notified yet.

        Args:
            limit: Maximum number of articles to retrieve (None for all)

        Returns:
            List of article dictionaries

        Example:
            >>> articles = db.get_unnotified_articles(limit=10)
            >>> for article in articles:
            ...     send_notification(article)
            ...     db.mark_as_notified(article['id'])
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id, article_id, title, url, published_date,
                       matched_keyword, full_content, created_at
                FROM articles
                WHERE notified = FALSE
                ORDER BY created_at DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def mark_as_notified(self, article_id: int) -> None:
        """
        Mark an article as notified.

        Args:
            article_id: Database ID of the article (not article_id field)

        Example:
            >>> db.mark_as_notified(article['id'])
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articles
                SET notified = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (article_id,))
            logger.debug(f"Marked article {article_id} as notified")

    def mark_multiple_as_notified(self, article_ids: List[int]) -> None:
        """
        Mark multiple articles as notified in a single transaction.

        Args:
            article_ids: List of database IDs to mark as notified

        Example:
            >>> ids = [article['id'] for article in articles]
            >>> db.mark_multiple_as_notified(ids)
        """
        if not article_ids:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(article_ids))
            cursor.execute(f"""
                UPDATE articles
                SET notified = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            """, article_ids)
            logger.info(f"Marked {len(article_ids)} articles as notified")

    def log_monitoring_run(
        self,
        articles_found: int,
        new_articles: int,
        status: str,
        error_message: Optional[str] = None,
        execution_time: Optional[float] = None
    ) -> None:
        """
        Log a monitoring run to the database.

        Args:
            articles_found: Total number of articles found
            new_articles: Number of new articles detected
            status: Status of the run ('success', 'error', 'partial')
            error_message: Error message if status is 'error'
            execution_time: Execution time in seconds

        Example:
            >>> db.log_monitoring_run(
            ...     articles_found=50,
            ...     new_articles=3,
            ...     status='success',
            ...     execution_time=12.5
            ... )
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO monitoring_logs (
                    articles_found, new_articles, status,
                    error_message, execution_time_seconds
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                articles_found,
                new_articles,
                status,
                error_message,
                execution_time
            ))
            logger.debug(f"Logged monitoring run: {status}")

    def get_monitoring_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get monitoring statistics for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary containing statistics

        Example:
            >>> stats = db.get_monitoring_stats(days=7)
            >>> print(f"Success rate: {stats['success_rate']:.2%}")
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            since_date = datetime.now() - timedelta(days=days)

            cursor.execute("""
                SELECT
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
                    SUM(new_articles) as total_new_articles,
                    AVG(execution_time_seconds) as avg_execution_time,
                    MAX(check_time) as last_check
                FROM monitoring_logs
                WHERE check_time >= ?
            """, (since_date,))

            row = cursor.fetchone()

            if row and row['total_runs'] > 0:
                return {
                    'total_runs': row['total_runs'],
                    'successful_runs': row['successful_runs'],
                    'success_rate': row['successful_runs'] / row['total_runs'],
                    'total_new_articles': row['total_new_articles'] or 0,
                    'avg_execution_time': row['avg_execution_time'] or 0,
                    'last_check': row['last_check']
                }

            return {
                'total_runs': 0,
                'successful_runs': 0,
                'success_rate': 0.0,
                'total_new_articles': 0,
                'avg_execution_time': 0.0,
                'last_check': None
            }

    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Delete records older than specified days.

        Args:
            days: Number of days to keep (default: 90)

        Returns:
            Number of records deleted

        Example:
            >>> deleted = db.cleanup_old_records(days=90)
            >>> print(f"Deleted {deleted} old records")
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)

            # Delete old articles that have been notified
            cursor.execute("""
                DELETE FROM articles
                WHERE created_at < ? AND notified = TRUE
            """, (cutoff_date,))
            articles_deleted = cursor.rowcount

            # Delete old monitoring logs
            cursor.execute("""
                DELETE FROM monitoring_logs
                WHERE check_time < ?
            """, (cutoff_date,))
            logs_deleted = cursor.rowcount

            total_deleted = articles_deleted + logs_deleted
            logger.info(f"Cleanup: Deleted {articles_deleted} articles and {logs_deleted} logs")

            return total_deleted

    def get_article_count(self) -> Tuple[int, int]:
        """
        Get total and unnotified article counts.

        Returns:
            Tuple of (total_count, unnotified_count)

        Example:
            >>> total, unnotified = db.get_article_count()
            >>> print(f"Total: {total}, Pending: {unnotified}")
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM articles")
            total = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE notified = FALSE")
            unnotified = cursor.fetchone()['count']

            return total, unnotified

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the database.

        Args:
            backup_path: Path for backup file (auto-generated if None)

        Returns:
            Path to the backup file

        Example:
            >>> backup_file = db.backup_database()
            >>> print(f"Backup created: {backup_file}")
        """
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.db_path.parent}/backups/articles_backup_{timestamp}.db"

        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as source:
            backup_conn = sqlite3.connect(backup_path)
            source.backup(backup_conn)
            backup_conn.close()

        logger.info(f"Database backed up to {backup_path}")
        return str(backup_path)

    def __repr__(self) -> str:
        """String representation of Database object."""
        return f"Database(db_path='{self.db_path}')"


if __name__ == "__main__":
    # Test database functionality
    db = Database("data/test_articles.db")

    # Test adding an article
    test_article = {
        'article_id': 'test-001',
        'title': 'Test Article',
        'url': 'https://example.com/test-001',
        'matched_keyword': 'バンドー化学',
        'full_content': 'This is a test article content.'
    }

    if db.add_article(test_article):
        print("✓ Article added successfully")

    # Test retrieving unnotified articles
    unnotified = db.get_unnotified_articles()
    print(f"✓ Unnotified articles: {len(unnotified)}")

    # Test statistics
    stats = db.get_monitoring_stats(days=7)
    print(f"✓ Monitoring stats: {stats}")

    # Test counts
    total, pending = db.get_article_count()
    print(f"✓ Articles - Total: {total}, Pending: {pending}")
