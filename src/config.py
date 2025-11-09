"""
Configuration Management Module

This module handles loading and managing configuration from:
1. config.yaml file
2. Environment variables (.env file)
3. Command-line arguments (via main.py)

Environment variables take precedence over config.yaml values.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager with support for YAML files and environment variables.

    Attributes:
        config_path (Path): Path to the configuration YAML file
        config (dict): Loaded configuration dictionary
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to the YAML configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

        # Load environment variables from .env file
        load_dotenv()

        # Load configuration
        self._load_config()
        self._validate_config()

    def _load_config(self) -> None:
        """
        Load configuration from YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create config.yaml based on the project template."
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in config file: {e}")

    def _validate_config(self) -> None:
        """
        Validate required configuration fields.

        Raises:
            ValueError: If required configuration is missing
        """
        required_sections = ['site', 'monitoring', 'email', 'scraping', 'database', 'logging']
        missing_sections = [s for s in required_sections if s not in self.config]

        if missing_sections:
            raise ValueError(
                f"Missing required configuration sections: {', '.join(missing_sections)}"
            )

        # Validate critical fields
        if not self.config['site'].get('url'):
            raise ValueError("site.url is required in configuration")

        if not self.config['site'].get('keywords'):
            raise ValueError("site.keywords is required in configuration")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'site.url')
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default

        Examples:
            >>> config.get('site.url')
            'https://gomuhouchi.com/'
            >>> config.get('monitoring.check_interval_minutes', 60)
            60
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    # Site configuration
    @property
    def site_url(self) -> str:
        """Get the target site URL."""
        return self.get('site.url')

    @property
    def keywords(self) -> List[str]:
        """Get the list of keywords to monitor."""
        return self.get('site.keywords', [])

    @property
    def urgent_keywords(self) -> List[str]:
        """Get the list of urgent keywords for immediate notification."""
        return self.get('site.urgent_keywords', [])

    @property
    def login_url(self) -> str:
        """Get the login page URL."""
        return self.get('site.login_url', self.site_url)

    # Credentials from environment variables
    @property
    def login_email(self) -> Optional[str]:
        """Get login email from environment variable."""
        return os.getenv('LOGIN_EMAIL')

    @property
    def login_password(self) -> Optional[str]:
        """Get login password from environment variable."""
        return os.getenv('LOGIN_PASSWORD')

    # Authentication configuration
    @property
    def auth_enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self.get('auth.enabled', True)

    @property
    def auth_max_retries(self) -> int:
        """Get maximum authentication retry attempts."""
        return self.get('auth.max_retries', 3)

    @property
    def auth_continue_on_failure(self) -> bool:
        """Check if scraping should continue when authentication fails."""
        return self.get('auth.continue_on_failure', True)

    # Monitoring configuration
    @property
    def check_interval_minutes(self) -> int:
        """Get the monitoring check interval in minutes."""
        return self.get('monitoring.check_interval_minutes', 60)

    @property
    def request_timeout(self) -> int:
        """Get request timeout in seconds."""
        return self.get('monitoring.request_timeout_seconds', 30)

    @property
    def max_retries(self) -> int:
        """Get maximum number of retries for failed requests."""
        return self.get('monitoring.max_retries', 3)

    # Email configuration
    @property
    def smtp_server(self) -> str:
        """Get SMTP server address."""
        return os.getenv('SMTP_SERVER', self.get('email.smtp_server'))

    @property
    def smtp_port(self) -> int:
        """Get SMTP server port."""
        return int(os.getenv('SMTP_PORT', self.get('email.smtp_port', 587)))

    @property
    def use_tls(self) -> bool:
        """Check if TLS should be used for SMTP."""
        return self.get('email.use_tls', True)

    @property
    def email_from(self) -> Optional[str]:
        """Get sender email address from environment."""
        return os.getenv('EMAIL_FROM')

    @property
    def email_password(self) -> Optional[str]:
        """Get email password from environment."""
        return os.getenv('EMAIL_PASSWORD')

    @property
    def email_to(self) -> Optional[str]:
        """Get recipient email address from environment."""
        return os.getenv('EMAIL_TO')

    @property
    def email_recipients(self) -> List[str]:
        """Get list of email recipients."""
        email_to = self.email_to
        if email_to:
            return [e.strip() for e in email_to.split(',')]
        return []

    @property
    def batch_notifications(self) -> bool:
        """Check if batch notifications are enabled."""
        return self.get('email.batch_notifications', True)

    @property
    def max_articles_per_email(self) -> int:
        """Get maximum articles per email."""
        return self.get('email.max_articles_per_email', 10)

    # Scraping configuration
    @property
    def headless(self) -> bool:
        """Check if browser should run in headless mode."""
        return self.get('scraping.headless', True)

    @property
    def user_agent_rotation(self) -> bool:
        """Check if user agent rotation is enabled."""
        return self.get('scraping.user_agent_rotation', True)

    @property
    def delay_min(self) -> int:
        """Get minimum delay between requests in seconds."""
        return self.get('scraping.delay_between_requests_min', 1)

    @property
    def delay_max(self) -> int:
        """Get maximum delay between requests in seconds."""
        return self.get('scraping.delay_between_requests_max', 3)

    @property
    def max_pages(self) -> int:
        """Get maximum pages to scrape."""
        return self.get('scraping.max_pages_to_scrape', 5)

    # Database configuration
    @property
    def db_path(self) -> str:
        """Get database file path."""
        return self.get('database.path', 'data/articles.db')

    @property
    def cleanup_enabled(self) -> bool:
        """Check if database cleanup is enabled."""
        return self.get('database.cleanup_enabled', True)

    @property
    def keep_records_days(self) -> int:
        """Get number of days to keep records."""
        return self.get('database.keep_records_days', 90)

    # Logging configuration
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get('logging.level', 'INFO')

    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.get('logging.file', 'logs/monitor.log')

    @property
    def log_max_bytes(self) -> int:
        """Get maximum log file size in bytes."""
        return self.get('logging.max_bytes', 10485760)

    @property
    def log_backup_count(self) -> int:
        """Get number of log backup files to keep."""
        return self.get('logging.backup_count', 5)

    @property
    def console_output(self) -> bool:
        """Check if console output is enabled."""
        return self.get('logging.console_output', True)

    @property
    def colored_output(self) -> bool:
        """Check if colored console output is enabled."""
        return self.get('logging.colored_output', True)

    # Feature flags
    @property
    def telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled."""
        return self.get('features.telegram_enabled', False)

    @property
    def telegram_bot_token(self) -> Optional[str]:
        """Get Telegram bot token."""
        return os.getenv('TELEGRAM_BOT_TOKEN', self.get('features.telegram_bot_token'))

    @property
    def telegram_chat_id(self) -> Optional[str]:
        """Get Telegram chat ID."""
        return os.getenv('TELEGRAM_CHAT_ID', self.get('features.telegram_chat_id'))

    @property
    def collect_metrics(self) -> bool:
        """Check if performance metrics collection is enabled."""
        return self.get('features.collect_metrics', True)

    def __repr__(self) -> str:
        """String representation of Config object."""
        return f"Config(config_path='{self.config_path}')"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Configuration loaded from {self.config_path}"


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = Config()
        print(f"✓ Configuration loaded successfully")
        print(f"  Site URL: {config.site_url}")
        print(f"  Keywords: {', '.join(config.keywords)}")
        print(f"  Check interval: {config.check_interval_minutes} minutes")
        print(f"  Database: {config.db_path}")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
