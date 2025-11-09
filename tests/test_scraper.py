"""
Unit tests for the scraper module.

Run with: pytest tests/test_scraper.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper import NewsScraper
from src.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock(spec=Config)
    config.site_url = "https://gomuhouchi.com/"
    config.keywords = ["バンドー化学", "三ツ星ベルト"]
    config.urgent_keywords = []
    config.headless = True
    config.user_agent_rotation = False
    config.delay_min = 0
    config.delay_max = 0
    config.max_pages = 2
    config.request_timeout = 10
    return config


@pytest.fixture
def scraper(mock_config):
    """Create a scraper instance with mock config."""
    return NewsScraper(mock_config)


def test_scraper_initialization(scraper, mock_config):
    """Test scraper initializes correctly."""
    assert scraper.config == mock_config
    assert scraper.driver is None
    assert scraper.authenticator is None


def test_generate_article_id(scraper):
    """Test article ID generation."""
    url = "https://example.com/article-1"
    title = "Test Article"

    article_id_1 = scraper._generate_article_id(url, title)
    article_id_2 = scraper._generate_article_id(url, title)

    # Same input should produce same ID
    assert article_id_1 == article_id_2

    # Different input should produce different ID
    article_id_3 = scraper._generate_article_id(url, "Different Title")
    assert article_id_1 != article_id_3


def test_filter_by_keywords(scraper):
    """Test keyword filtering."""
    articles = [
        {
            'title': 'バンドー化学が新製品を発表',
            'summary': 'Details about the product',
            'url': 'https://example.com/1'
        },
        {
            'title': 'Other company news',
            'summary': 'No relevant keywords',
            'url': 'https://example.com/2'
        },
        {
            'title': 'News about 三ツ星ベルト',
            'summary': 'Some details',
            'url': 'https://example.com/3'
        }
    ]

    matched = scraper._filter_by_keywords(articles)

    assert len(matched) == 2
    assert matched[0]['matched_keyword'] == 'バンドー化学'
    assert matched[1]['matched_keyword'] == '三ツ星ベルト'


def test_parse_date(scraper):
    """Test date parsing."""
    # ISO format
    date1 = scraper._parse_date("2024-01-15")
    assert date1 is not None

    # Japanese format
    date2 = scraper._parse_date("2024年01月15日")
    assert date2 is not None

    # Invalid format
    date3 = scraper._parse_date("invalid date")
    assert date3 == "invalid date"


def test_get_page_url(scraper, mock_config):
    """Test page URL generation."""
    url1 = scraper._get_page_url(1)
    assert url1 == "https://gomuhouchi.com"

    url2 = scraper._get_page_url(2)
    assert "page/2" in url2


@pytest.mark.parametrize("keyword,text,should_match", [
    ("バンドー化学", "バンドー化学の新製品", True),
    ("三ツ星ベルト", "株式会社三ツ星ベルト", True),
    ("テスト", "関係ない記事", False),
])
def test_keyword_matching(scraper, keyword, text, should_match):
    """Test keyword matching with various inputs."""
    scraper.config.keywords = [keyword]
    scraper.config.urgent_keywords = []

    articles = [{'title': text, 'summary': ''}]
    matched = scraper._filter_by_keywords(articles)

    if should_match:
        assert len(matched) == 1
    else:
        assert len(matched) == 0


def test_scraper_context_manager(mock_config):
    """Test scraper as context manager."""
    with patch.object(NewsScraper, 'start'), \
         patch.object(NewsScraper, 'stop'):

        with NewsScraper(mock_config) as scraper:
            assert scraper is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
