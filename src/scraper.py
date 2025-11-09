"""
Web Scraping Module

This module handles scraping of articles from gomuhouchi.com with features:
- Selenium-based dynamic content scraping
- Keyword matching and filtering
- Article content extraction
- Rate limiting and error handling
- User-agent rotation
"""

import logging
import time
import re
import hashlib
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Custom exception for scraping failures."""
    pass


class NewsScraper:
    """
    News scraper for gomuhouchi.com with keyword monitoring.

    Attributes:
        config: Configuration object
        driver: Selenium WebDriver instance
        user_agent: UserAgent instance for rotation
    """

    def __init__(self, config, authenticator=None):
        """
        Initialize the news scraper.

        Args:
            config: Configuration object
            authenticator: Optional Authenticator instance for login

        Example:
            >>> scraper = NewsScraper(config)
            >>> articles = scraper.scrape_articles()
        """
        self.config = config
        self.authenticator = authenticator
        self.driver = None
        self.user_agent = UserAgent() if config.user_agent_rotation else None

    def _setup_driver(self) -> webdriver.Chrome:
        """
        Setup and configure Chrome WebDriver.

        Returns:
            Configured Chrome WebDriver instance

        Raises:
            WebDriverException: If driver setup fails
        """
        try:
            chrome_options = Options()

            # Headless mode
            if self.config.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')

            # Common options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--window-size=1920,1080')

            # User agent
            if self.user_agent:
                user_agent_string = self.user_agent.random
                chrome_options.add_argument(f'user-agent={user_agent_string}')
                logger.debug(f"Using User-Agent: {user_agent_string[:50]}...")

            # Disable images for faster loading (optional)
            # chrome_options.add_argument('--blink-settings=imagesEnabled=false')

            # Setup service - use system chromedriver in GitHub Actions
            if os.getenv('GITHUB_ACTIONS') == 'true':
                # GitHub Actions: Use system-installed chromedriver
                logger.info("GitHub Actions detected - using system chromedriver")
                # Don't specify service, let Selenium find chromedriver in PATH
                driver = webdriver.Chrome(options=chrome_options)
            else:
                # Local environment: Use webdriver-manager
                logger.info("Local environment - using webdriver-manager")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.set_page_load_timeout(self.config.request_timeout)
            driver.implicitly_wait(10)

            logger.info("WebDriver initialized successfully")
            return driver

        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise WebDriverException(f"Driver setup failed: {e}")

    def start(self) -> None:
        """
        Start the scraper (initialize driver and login if needed).

        Example:
            >>> scraper.start()
            >>> articles = scraper.scrape_articles()
            >>> scraper.stop()
        """
        if self.driver is None:
            self.driver = self._setup_driver()

            # Login if authenticator is provided
            if self.authenticator and not self.authenticator.is_authenticated:
                logger.info("Performing authentication...")
                self.authenticator.login()

    def stop(self) -> None:
        """
        Stop the scraper (close driver).

        Example:
            >>> scraper.stop()
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriver closed")

    def scrape_articles(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape articles from the website and filter by keywords.

        Args:
            max_pages: Maximum number of pages to scrape (None for config default)

        Returns:
            List of article dictionaries matching keywords

        Raises:
            ScrapingError: If scraping fails

        Example:
            >>> articles = scraper.scrape_articles(max_pages=3)
            >>> for article in articles:
            ...     print(article['title'], article['matched_keyword'])
        """
        if self.driver is None:
            self.start()

        max_pages = max_pages or self.config.max_pages
        all_articles = []

        try:
            logger.info(f"Starting scrape of {self.config.site_url}")

            for page_num in range(1, max_pages + 1):
                logger.info(f"Scraping page {page_num}/{max_pages}")

                # Navigate to page
                page_url = self._get_page_url(page_num)
                self.driver.get(page_url)

                # Random delay to avoid detection
                self._random_delay()

                # Extract articles from current page
                page_articles = self._extract_articles_from_page()

                if not page_articles:
                    logger.info(f"No more articles found on page {page_num}")
                    break

                all_articles.extend(page_articles)
                logger.info(f"Found {len(page_articles)} articles on page {page_num}")

                # Check if there's a next page
                if not self._has_next_page():
                    logger.info("Reached last page")
                    break

            # Filter articles by keywords
            matched_articles = self._filter_by_keywords(all_articles)
            logger.info(f"Total: {len(all_articles)} articles, Matched: {len(matched_articles)}")

            return matched_articles

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise ScrapingError(f"Failed to scrape articles: {e}")

    def _get_page_url(self, page_num: int) -> str:
        """
        Get URL for specific page number.

        Args:
            page_num: Page number (1-indexed)

        Returns:
            Full URL for the page

        Note:
            This may need customization based on actual site structure
        """
        base_url = self.config.site_url.rstrip('/')

        if page_num == 1:
            return base_url
        else:
            # Common pagination patterns - adjust based on actual site
            return f"{base_url}/page/{page_num}"
            # Alternative: return f"{base_url}?page={page_num}"

    def _extract_articles_from_page(self) -> List[Dict[str, Any]]:
        """
        Extract article information from current page.

        Returns:
            List of article dictionaries

        Note:
            This method contains site-specific selectors that may need adjustment
        """
        articles = []

        try:
            # Wait for articles to load
            wait = WebDriverWait(self.driver, 10)

            # Common article container selectors (try multiple)
            article_selectors = [
                'article',
                '.article',
                '.post',
                '.news-item',
                '.entry',
                '[class*="article"]',
            ]

            article_elements = None
            for selector in article_selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    article_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if article_elements:
                        logger.debug(f"Found {len(article_elements)} articles using selector: {selector}")
                        break
                except TimeoutException:
                    continue

            if not article_elements:
                logger.warning("No article elements found on page")
                return []

            # Parse each article
            for element in article_elements:
                try:
                    article = self._parse_article_element(element)
                    if article:
                        articles.append(article)
                except StaleElementReferenceException:
                    logger.debug("Stale element encountered, skipping")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse article element: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to extract articles: {e}")

        return articles

    def _parse_article_element(self, element) -> Optional[Dict[str, Any]]:
        """
        Parse individual article element to extract information.

        Args:
            element: Selenium WebElement representing an article

        Returns:
            Dictionary with article information or None if parsing fails

        Note:
            Selectors may need adjustment based on actual site structure
        """
        try:
            # Get article HTML for BeautifulSoup parsing
            html = element.get_attribute('outerHTML')
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title
            title = None
            title_selectors = ['h2', 'h3', '.title', '.headline', 'a']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break

            if not title:
                logger.debug("Article title not found")
                return None

            # Extract URL
            url = None
            link = soup.find('a', href=True)
            if link:
                url = urljoin(self.config.site_url, link['href'])
            else:
                logger.debug("Article URL not found")
                return None

            # Extract date (if available)
            published_date = None
            date_selectors = ['.date', '.published', 'time', '[datetime]']
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    published_date = self._parse_date(date_text)
                    break

            # Extract summary/excerpt
            summary = None
            summary_selectors = ['.excerpt', '.summary', 'p']
            for selector in summary_selectors:
                summary_elem = soup.select_one(selector)
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)
                    break

            # Generate unique article ID
            article_id = self._generate_article_id(url, title)

            # Check if member-only article
            is_member_only = self._is_member_only_article(soup, title, summary or '')

            return {
                'article_id': article_id,
                'title': title,
                'url': url,
                'published_date': published_date,
                'summary': summary or '',
                'full_content': None,  # Will be fetched later if needed
                'is_member_only': is_member_only
            }

        except Exception as e:
            logger.debug(f"Failed to parse article element: {e}")
            return None

    def _filter_by_keywords(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter articles that match configured keywords.

        Args:
            articles: List of article dictionaries

        Returns:
            List of articles matching keywords with matched_keyword field added
        """
        matched_articles = []
        keywords = self.config.keywords + self.config.urgent_keywords

        for article in articles:
            # Check title and summary for keywords
            text_to_search = f"{article['title']} {article.get('summary', '')}".lower()

            for keyword in keywords:
                if keyword.lower() in text_to_search:
                    article['matched_keyword'] = keyword
                    article['is_urgent'] = keyword in self.config.urgent_keywords
                    matched_articles.append(article)
                    logger.debug(f"Article matched keyword '{keyword}': {article['title']}")
                    break  # Only match first keyword

        return matched_articles

    def fetch_full_content(self, article_url: str) -> str:
        """
        Fetch full article content from article page.

        Args:
            article_url: URL of the article

        Returns:
            Full article content as text

        Example:
            >>> content = scraper.fetch_full_content(article['url'])
        """
        try:
            logger.debug(f"Fetching full content from: {article_url}")
            self.driver.get(article_url)
            self._random_delay()

            # Wait for content to load
            wait = WebDriverWait(self.driver, 10)

            # Common content selectors
            content_selectors = [
                '.article-content',
                '.entry-content',
                '.post-content',
                'article .content',
                '[class*="content"]',
            ]

            content = None
            for selector in content_selectors:
                try:
                    content_elem = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    content = content_elem.text
                    break
                except TimeoutException:
                    continue

            if not content:
                # Fallback: get all paragraph text
                paragraphs = self.driver.find_elements(By.TAG_NAME, 'p')
                content = '\n\n'.join([p.text for p in paragraphs if p.text.strip()])

            return content.strip()

        except Exception as e:
            logger.error(f"Failed to fetch full content: {e}")
            return ""

    def _has_next_page(self) -> bool:
        """
        Check if there's a next page available.

        Returns:
            bool: True if next page exists

        Note:
            This may need customization based on actual site pagination
        """
        try:
            # Common "next page" selectors
            next_page_selectors = [
                'a.next',
                'a[rel="next"]',
                '.pagination .next',
                'a:contains("次へ")',  # Japanese "next"
                'a:contains("Next")',
            ]

            for selector in next_page_selectors:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, selector)
                    return True
                except NoSuchElementException:
                    continue

            return False

        except Exception:
            return False

    def _random_delay(self) -> None:
        """
        Add random delay between requests to avoid detection.
        """
        delay = random.uniform(self.config.delay_min, self.config.delay_max)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)

    def _generate_article_id(self, url: str, title: str) -> str:
        """
        Generate unique article ID from URL and title.

        Args:
            url: Article URL
            title: Article title

        Returns:
            Unique article ID (MD5 hash)
        """
        content = f"{url}|{title}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def _parse_date(self, date_string: str) -> Optional[str]:
        """
        Parse date string to ISO format.

        Args:
            date_string: Date string in various formats

        Returns:
            ISO format date string or None if parsing fails
        """
        try:
            # Try common date formats
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',  # Japanese format
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_string[:19], fmt)
                    return dt.isoformat()
                except ValueError:
                    continue

            # If all else fails, return original
            return date_string

        except Exception:
            return None

    def _is_member_only_article(self, soup: BeautifulSoup, title: str, summary: str) -> bool:
        """
        Detect if article is member-only.

        Args:
            soup: BeautifulSoup object of article element
            title: Article title
            summary: Article summary

        Returns:
            bool: True if article is member-only

        Example:
            >>> is_member = scraper._is_member_only_article(soup, title, summary)
        """
        # Check for member-only indicators in text
        member_indicators = [
            '会員限定',  # Member limited (Japanese)
            '会員専用',  # Member exclusive (Japanese)
            'プレミアム',  # Premium (Japanese)
            '有料会員',  # Paid member (Japanese)
            '登録会員',  # Registered member (Japanese)
            'member-only',
            'premium',
            'subscription'
        ]

        # Check in title and summary
        text_to_check = f"{title} {summary}".lower()
        for indicator in member_indicators:
            if indicator.lower() in text_to_check:
                logger.debug(f"Member-only indicator found in text: {indicator}")
                return True

        # Check for CSS classes
        article_html = str(soup)
        class_indicators = [
            'member-only',
            'premium',
            'subscriber-only',
            'paywall',
            'locked'
        ]

        for indicator in class_indicators:
            if indicator in article_html.lower():
                logger.debug(f"Member-only indicator found in HTML: {indicator}")
                return True

        # Check for lock icons or indicators
        if '🔒' in text_to_check or '&#128274;' in article_html:
            logger.debug("Lock icon found - member-only article")
            return True

        return False

    def fetch_article_content_with_login_check(self, article_url: str) -> Optional[str]:
        """
        Fetch full article content with login requirement detection.

        This method is an enhanced version of fetch_full_content that detects
        if login is required and returns None if content is not accessible.

        Args:
            article_url: URL of the article

        Returns:
            Full article content or None if login required

        Example:
            >>> content = scraper.fetch_article_content_with_login_check(url)
            >>> if content is None:
            ...     print("Login required for this article")
        """
        try:
            logger.debug(f"Fetching content from: {article_url}")
            self.driver.get(article_url)
            self._random_delay()

            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)

            # Check for login required messages
            login_indicators = [
                'ログインが必要です',  # Login required (Japanese)
                'ログインしてください',  # Please login (Japanese)
                '会員登録が必要',  # Membership required (Japanese)
                'この記事を読むには',  # To read this article (Japanese)
                'login required',
                'sign in to read',
                'subscription required'
            ]

            page_source = self.driver.page_source.lower()
            for indicator in login_indicators:
                if indicator.lower() in page_source:
                    logger.warning(f"Login required for article: {article_url}")
                    return None

            # Try to fetch content using existing method
            content = self.fetch_full_content(article_url)

            # Additional check: if content is too short, might be paywalled
            if content and len(content) < 100:
                logger.warning(f"Content too short, might be paywalled: {article_url}")
                return None

            return content

        except Exception as e:
            logger.error(f"Failed to fetch content with login check: {e}")
            return None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def __repr__(self) -> str:
        """String representation of NewsScraper object."""
        status = "active" if self.driver else "inactive"
        return f"NewsScraper(status={status})"


if __name__ == "__main__":
    # Test scraper
    from .config import Config

    print("Testing scraper module...")
    config = Config()

    with NewsScraper(config) as scraper:
        articles = scraper.scrape_articles(max_pages=1)
        print(f"Found {len(articles)} articles")

        for article in articles[:3]:
            print(f"\nTitle: {article['title']}")
            print(f"URL: {article['url']}")
            print(f"Keyword: {article['matched_keyword']}")
