"""
Gomu News Monitor - Main Entry Point

A production-grade monitoring system for gomuhouchi.com news articles.
Monitors specified keywords and sends email notifications for new articles.

Usage:
    python main.py --mode test          # Run once for testing
    python main.py --mode daemon        # Run continuously (daemon mode)
    python main.py --keywords keyword   # Override keywords
    python main.py --interactive        # Interactive credential input
"""

import argparse
import logging
import sys
import os
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import traceback

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.database import Database
from src.auth import Authenticator, AuthenticationError
from src.scraper import NewsScraper, ScrapingError
from src.notifier import Notifier, NotificationError


class GomuNewsMonitor:
    """
    Main monitoring application coordinator.

    Orchestrates scraping, database operations, and notifications.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the monitoring system.

        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        self.database = Database(self.config.db_path)
        self.notifier = Notifier(self.config)
        self.scraper: Optional[NewsScraper] = None
        self.authenticator: Optional[Authenticator] = None
        self.running = False
        self.logger = logging.getLogger(__name__)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def run_once(self) -> Dict[str, Any]:
        """
        Run monitoring cycle once.

        Returns:
            Dictionary with run statistics

        Example:
            >>> monitor = GomuNewsMonitor()
            >>> stats = monitor.run_once()
            >>> print(f"Found {stats['new_articles']} new articles")
        """
        start_time = time.time()
        stats = {
            'articles_found': 0,
            'new_articles': 0,
            'notifications_sent': 0,
            'status': 'success',
            'error_message': None
        }

        try:
            self.logger.info("=" * 60)
            self.logger.info(f"Starting monitoring cycle: {datetime.now()}")
            self.logger.info("=" * 60)

            # Initialize scraper
            self.logger.info("Initializing web scraper...")
            self.scraper = NewsScraper(self.config)
            self.scraper.start()

            # Authenticate if enabled and credentials are configured
            if self.config.auth_enabled and self.config.login_email and self.config.login_password:
                self.logger.info("Authenticating...")
                self.authenticator = Authenticator(self.config, self.scraper.driver)
                try:
                    self.authenticator.login()
                    self.logger.info("Authentication successful")
                except AuthenticationError as e:
                    self.logger.warning(f"Authentication failed: {e}")
                    if self.config.auth_continue_on_failure:
                        self.logger.info("Continuing without authentication (public articles only)")
                    else:
                        raise
            elif not self.config.auth_enabled:
                self.logger.info("Authentication disabled - scraping public articles only")
            else:
                self.logger.warning("Login credentials not configured - scraping public articles only")

            # Scrape articles
            self.logger.info("Scraping articles...")
            articles = self.scraper.scrape_articles()
            stats['articles_found'] = len(articles)

            self.logger.info(f"Found {len(articles)} articles matching keywords")

            # Process new articles
            new_articles = []
            for article in articles:
                if not self.database.article_exists(article['article_id']):
                    # Optionally fetch full content
                    if self.config.get('email.include_full_content', False):
                        self.logger.debug(f"Fetching full content for: {article['title']}")
                        article['full_content'] = self.scraper.fetch_full_content(article['url'])

                    # Add to database
                    if self.database.add_article(article):
                        new_articles.append(article)
                        self.logger.info(f"New article: {article['title']}")

            stats['new_articles'] = len(new_articles)

            # Translate new article titles to Korean
            if new_articles and self.config.get('translation.enabled', True):
                self.logger.info(f"Translating {len(new_articles)} article titles...")
                try:
                    from src.translator import get_translator
                    translator = get_translator()

                    translated_count = 0
                    failed_count = 0

                    for article in new_articles:
                        try:
                            title_ko = translator.translate(article['title'])
                            if title_ko:
                                article['title_ko'] = title_ko
                                # Update database with translation
                                self.database.update_article_translation(
                                    article['article_id'],
                                    title_ko
                                )
                                translated_count += 1
                            else:
                                article['title_ko'] = None
                                failed_count += 1
                                self.logger.warning(f"Translation failed for: {article['title'][:50]}...")
                        except Exception as e:
                            article['title_ko'] = None
                            failed_count += 1
                            self.logger.error(f"Translation error: {e}")

                    self.logger.info(f"Translation complete: {translated_count} successful, {failed_count} failed")

                except Exception as e:
                    self.logger.error(f"Translation module error: {e}")
                    # Continue without translations
                    for article in new_articles:
                        article['title_ko'] = None

            # Send notifications for new articles
            if new_articles:
                self.logger.info(f"Sending notifications for {len(new_articles)} new articles...")

                if self.notifier.send_article_notifications(new_articles):
                    # Mark articles as notified
                    article_ids = [a['article_id'] for a in new_articles]

                    # Get database IDs for the articles we just added
                    unnotified = self.database.get_unnotified_articles()
                    db_ids = [a['id'] for a in unnotified if a['article_id'] in article_ids]

                    self.database.mark_multiple_as_notified(db_ids)
                    stats['notifications_sent'] = len(new_articles)
                    self.logger.info("Notifications sent successfully")
                else:
                    self.logger.warning("Failed to send notifications")
                    stats['status'] = 'partial'
            else:
                self.logger.info("No new articles to notify about")

            # Cleanup old records if enabled
            if self.config.cleanup_enabled:
                deleted = self.database.cleanup_old_records(self.config.keep_records_days)
                if deleted > 0:
                    self.logger.info(f"Cleaned up {deleted} old records")

        except ScrapingError as e:
            self.logger.error(f"Scraping error: {e}")
            stats['status'] = 'error'
            stats['error_message'] = str(e)
            self._handle_error(e)

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.logger.debug(traceback.format_exc())
            stats['status'] = 'error'
            stats['error_message'] = str(e)
            self._handle_error(e)

        finally:
            # Cleanup
            if self.scraper:
                self.scraper.stop()

            # Log monitoring run
            execution_time = time.time() - start_time
            stats['execution_time'] = execution_time

            self.database.log_monitoring_run(
                articles_found=stats['articles_found'],
                new_articles=stats['new_articles'],
                status=stats['status'],
                error_message=stats['error_message'],
                execution_time=execution_time
            )

            self.logger.info("-" * 60)
            self.logger.info(f"Monitoring cycle completed in {execution_time:.2f}s")
            self.logger.info(f"Articles found: {stats['articles_found']}, "
                           f"New: {stats['new_articles']}, "
                           f"Notified: {stats['notifications_sent']}")
            self.logger.info("-" * 60)

        return stats

    def run_daemon(self) -> None:
        """
        Run monitoring in daemon mode (continuous loop).

        This will run indefinitely until interrupted.

        Example:
            >>> monitor = GomuNewsMonitor()
            >>> monitor.run_daemon()  # Runs until Ctrl+C
        """
        self.running = True
        consecutive_errors = 0
        max_consecutive_errors = 5

        self.logger.info("Starting daemon mode...")
        self.logger.info(f"Check interval: {self.config.check_interval_minutes} minutes")

        while self.running:
            try:
                stats = self.run_once()

                if stats['status'] == 'success':
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    self.logger.warning(f"Consecutive errors: {consecutive_errors}/{max_consecutive_errors}")

                    if consecutive_errors >= max_consecutive_errors:
                        self.logger.critical(f"Too many consecutive errors ({consecutive_errors}), stopping daemon")
                        self.notifier.send_error_notification(
                            f"Monitoring daemon stopped after {consecutive_errors} consecutive errors.\n"
                            f"Last error: {stats['error_message']}"
                        )
                        break

            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
                break

            except Exception as e:
                self.logger.error(f"Critical error in daemon loop: {e}")
                consecutive_errors += 1

            # Wait for next check
            if self.running:
                next_check = datetime.now()
                next_check = next_check.replace(
                    minute=(next_check.minute + self.config.check_interval_minutes) % 60
                )
                self.logger.info(f"Next check at: {next_check.strftime('%H:%M')}")
                self.logger.info(f"Waiting {self.config.check_interval_minutes} minutes...\n")

                # Sleep in small increments to allow for graceful shutdown
                sleep_time = self.config.check_interval_minutes * 60
                elapsed = 0
                while elapsed < sleep_time and self.running:
                    time.sleep(min(10, sleep_time - elapsed))
                    elapsed += 10

        self.logger.info("Daemon mode stopped")

    def _handle_error(self, error: Exception) -> None:
        """
        Handle errors by logging and optionally sending notifications.

        Args:
            error: The exception that occurred
        """
        error_msg = f"{type(error).__name__}: {str(error)}"

        # Check if we should send error notification
        if self.config.get('email.send_error_notifications', True):
            # Get recent error count
            stats = self.database.get_monitoring_stats(days=1)
            error_threshold = self.config.get('email.error_notification_threshold', 3)

            recent_total = stats.get('total_runs', 0)
            recent_success = stats.get('successful_runs', 0)
            recent_errors = recent_total - recent_success

            if recent_errors >= error_threshold:
                self.logger.info(f"Error threshold reached ({recent_errors}), sending notification")
                self.notifier.send_error_notification(error_msg)

    def print_statistics(self, days: int = 7) -> None:
        """
        Print monitoring statistics.

        Args:
            days: Number of days to look back

        Example:
            >>> monitor.print_statistics(days=7)
        """
        stats = self.database.get_monitoring_stats(days=days)
        total, pending = self.database.get_article_count()

        print("\n" + "=" * 60)
        print(f"Monitoring Statistics (Last {days} days)")
        print("=" * 60)
        print(f"Total monitoring runs:     {stats['total_runs']}")
        print(f"Successful runs:           {stats['successful_runs']}")
        print(f"Success rate:              {stats['success_rate']:.1%}")
        print(f"New articles found:        {stats['total_new_articles']}")
        print(f"Average execution time:    {stats['avg_execution_time']:.2f}s")
        print(f"Last check:                {stats['last_check'] or 'Never'}")
        print("-" * 60)
        print(f"Total articles in DB:      {total}")
        print(f"Pending notifications:     {pending}")
        print("=" * 60 + "\n")


def setup_logging(config: Config) -> None:
    """
    Setup logging configuration.

    Args:
        config: Configuration object
    """
    # Create logs directory
    log_file = Path(config.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # File handler
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.log_max_bytes,
        backupCount=config.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        if config.colored_output:
            try:
                import colorlog
                color_format = '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                console_handler.setFormatter(colorlog.ColoredFormatter(color_format))
            except ImportError:
                console_handler.setFormatter(logging.Formatter(log_format))
        else:
            console_handler.setFormatter(logging.Formatter(log_format))

        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=[file_handler, console_handler]
        )
    else:
        logging.basicConfig(
            level=log_level,
            handlers=[file_handler]
        )


def detect_github_actions_environment(logger: logging.Logger) -> bool:
    """
    Detect if running in GitHub Actions environment and log details.

    Args:
        logger: Logger instance for output

    Returns:
        bool: True if running in GitHub Actions, False otherwise
    """
    is_github_actions = os.getenv('GITHUB_ACTIONS', '').lower() == 'true'

    if is_github_actions:
        logger.info("=" * 60)
        logger.info("🔍 GitHub Actions Environment Detected")
        logger.info("=" * 60)

        # Log relevant GitHub Actions environment variables
        github_vars = {
            'Workflow': os.getenv('GITHUB_WORKFLOW'),
            'Repository': os.getenv('GITHUB_REPOSITORY'),
            'Run Number': os.getenv('GITHUB_RUN_NUMBER'),
            'Run ID': os.getenv('GITHUB_RUN_ID'),
            'Run Attempt': os.getenv('GITHUB_RUN_ATTEMPT'),
            'Actor': os.getenv('GITHUB_ACTOR'),
            'Event Name': os.getenv('GITHUB_EVENT_NAME'),
            'Ref': os.getenv('GITHUB_REF'),
            'SHA': os.getenv('GITHUB_SHA', '')[:8] if os.getenv('GITHUB_SHA') else None,
        }

        for key, value in github_vars.items():
            if value:
                logger.info(f"  {key}: {value}")

        # Set DEBUG logging level for better visibility in GitHub Actions logs
        root_logger = logging.getLogger()
        original_level = root_logger.level
        if original_level > logging.INFO:
            root_logger.setLevel(logging.INFO)
            logger.info("  Log level adjusted to INFO for GitHub Actions")

        logger.info("=" * 60)

    return is_github_actions


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Gomu News Monitor - Monitor gomuhouchi.com for new articles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode test              Run once for testing
  python main.py --mode daemon            Run continuously
  python main.py --stats                  Show statistics
  python main.py --test-email             Send test email
  python main.py --debug-login            Debug login page structure
        """
    )

    parser.add_argument(
        '--mode',
        choices=['test', 'daemon'],
        default='test',
        help='Execution mode: test (run once) or daemon (continuous)'
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics and exit'
    )

    parser.add_argument(
        '--test-email',
        action='store_true',
        help='Send test email and exit'
    )

    parser.add_argument(
        '--debug-login',
        action='store_true',
        help='Debug login page structure and exit'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days for statistics (default: 7)'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = Config(args.config)

        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)

        logger.info("=" * 60)
        logger.info("Gomu News Monitor v1.0")
        logger.info("=" * 60)

        # Detect GitHub Actions environment
        detect_github_actions_environment(logger)

        # Create monitor instance
        monitor = GomuNewsMonitor(args.config)

        # Handle different modes
        if args.stats:
            monitor.print_statistics(days=args.days)

        elif args.test_email:
            logger.info("Sending test email...")
            notifier = Notifier(config)
            if notifier.send_test_email():
                print("✓ Test email sent successfully!")
                print(f"  Check inbox: {', '.join(config.email_recipients)}")
            else:
                print("✗ Test email failed. Check logs for details.")
                sys.exit(1)

        elif args.debug_login:
            logger.info("Running login page debug mode...")
            print("\n" + "=" * 60)
            print("Login Page Debug Mode")
            print("=" * 60)

            # Initialize scraper
            scraper = NewsScraper(config)
            scraper.start()

            # Create authenticator and run debug
            authenticator = Authenticator(config, scraper.driver)

            try:
                print(f"\nAnalyzing login page: {config.login_url}\n")
                debug_info = authenticator.debug_login_page()

                print("\n" + "=" * 60)
                print("Debug Summary")
                print("=" * 60)
                print(f"Total input fields:  {len(debug_info['input_fields'])}")
                print(f"Total buttons:       {len(debug_info['buttons'])}")
                print(f"Total submit inputs: {len(debug_info['submit_buttons'])}")
                print(f"Total forms:         {len(debug_info['forms'])}")
                print("\n✓ Debug files created:")
                print("  - login_page_debug.html")
                print("  - login_debug_info.json")
                print("  - login_page_screenshot.png")
                print("\nPlease review these files and update src/auth.py with correct selectors.")
                print("=" * 60 + "\n")

            except Exception as e:
                print(f"✗ Debug failed: {e}")
                logger.error(f"Debug failed: {e}")
                sys.exit(1)
            finally:
                scraper.stop()

        elif args.mode == 'test':
            logger.info("Running in TEST mode (single run)")
            stats = monitor.run_once()
            monitor.print_statistics(days=1)

            if stats['status'] == 'success':
                sys.exit(0)
            else:
                sys.exit(1)

        elif args.mode == 'daemon':
            logger.info("Running in DAEMON mode (continuous)")
            monitor.run_daemon()

    except FileNotFoundError as e:
        print(f"✗ Configuration file not found: {e}")
        print("  Please create config.yaml based on the project template.")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
