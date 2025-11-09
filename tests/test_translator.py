"""
Test translation module.

This module tests the Japanese to Korean translation functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.translator import ArticleTranslator, get_translator, clear_translator_cache


class TestArticleTranslator:
    """Test cases for ArticleTranslator class."""

    def test_initialize_translator(self):
        """Test translator initialization."""
        translator = ArticleTranslator()
        assert translator is not None
        assert translator.translator is not None
        assert isinstance(translator.cache, dict)
        print("✓ Translator initialized successfully")

    def test_translate_simple(self):
        """Test simple translation."""
        translator = ArticleTranslator()
        text = "バンドー化学"
        result = translator.translate(text)

        assert result is not None
        assert len(result) > 0
        assert result != text  # Should be different from original

        print(f"✓ Translation: {text} → {result}")

    def test_translate_full_title(self):
        """Test full article title translation."""
        translator = ArticleTranslator()
        text = "バンドー化学、産業資材事業は増収大幅増益"
        result = translator.translate(text)

        assert result is not None
        assert len(result) > 0

        print(f"✓ Full title translation:")
        print(f"  Original: {text}")
        print(f"  Translated: {result}")

    def test_translate_cache(self):
        """Test translation caching."""
        translator = ArticleTranslator()
        text = "テスト"

        # First translation
        result1 = translator.translate(text)

        # Check cache
        assert text in translator.cache
        assert translator.cache[text] == result1

        # Second translation (should use cache)
        result2 = translator.translate(text)

        assert result1 == result2
        print(f"✓ Cache working: {text} → {result1}")

    def test_translate_empty(self):
        """Test empty text translation."""
        translator = ArticleTranslator()

        result_empty = translator.translate("")
        result_none = translator.translate(None)
        result_whitespace = translator.translate("   ")

        assert result_empty is None
        assert result_none is None
        assert result_whitespace is None

        print("✓ Empty text handling working")

    def test_translate_batch(self):
        """Test batch translation."""
        translator = ArticleTranslator()
        texts = [
            "三ツ星ベルト",
            "新製品",
            "開発中"
        ]

        results = translator.translate_batch(texts)

        assert len(results) == len(texts)
        for text in texts:
            assert text in results
            assert results[text] is not None
            print(f"  {text} → {results[text]}")

        print("✓ Batch translation working")

    def test_singleton_pattern(self):
        """Test singleton pattern for get_translator()."""
        translator1 = get_translator()
        translator2 = get_translator()

        assert translator1 is translator2
        print("✓ Singleton pattern working")

    def test_clear_cache(self):
        """Test cache clearing."""
        translator = get_translator()

        # Add some translations to cache
        translator.translate("テスト1")
        translator.translate("テスト2")

        initial_size = translator.get_cache_size()
        assert initial_size > 0

        # Clear cache
        translator.clear_cache()

        assert translator.get_cache_size() == 0
        print(f"✓ Cache cleared: {initial_size} → 0 entries")

    def test_real_article_titles(self):
        """Test with real article titles from gomuhouchi.com."""
        translator = ArticleTranslator()

        real_titles = [
            "バンドー化学、産業資材事業は増収大幅増益",
            "三ツ星ベルト、寄付金贈呈式とミュージックサロンを開催",
            "バンドー化学、物流分野は新製品「ミスターProキャリー」の販",
            "三ツ星ベルト、EPS向けベルトの生産設備を増強",
        ]

        print("\n✓ Real article title translations:")
        for title in real_titles:
            result = translator.translate(title)
            assert result is not None
            print(f"  原文: {title}")
            print(f"  번역: {result}")
            print()


class TestTranslatorIntegration:
    """Integration tests for translator."""

    def test_integration_with_database(self):
        """Test translator integration with database."""
        from src.config import Config
        from src.database import Database
        from src.translator import get_translator

        config = Config()
        db = Database(":memory:")  # Use in-memory database for testing
        translator = get_translator()

        # Create test article
        article = {
            'article_id': 'test-001',
            'title': 'バンドー化学テスト',
            'url': 'https://example.com/test',
            'matched_keyword': 'バンドー化学'
        }

        # Translate
        title_ko = translator.translate(article['title'])
        article['title_ko'] = title_ko

        # Save to database
        success = db.add_article(article)
        assert success

        # Retrieve from database
        articles = db.get_unnotified_articles()
        assert len(articles) == 1
        assert articles[0]['title_ko'] == title_ko

        print("✓ Database integration working")


def run_manual_tests():
    """Run manual tests with console output."""
    print("\n" + "=" * 60)
    print("Manual Translation Tests")
    print("=" * 60 + "\n")

    translator = get_translator()

    test_cases = [
        "バンドー化学",
        "三ツ星ベルト",
        "新製品発表",
        "生産設備増強",
        "リコール",
    ]

    for text in test_cases:
        result = translator.translate(text)
        print(f"{text:20s} → {result}")

    print(f"\nCache size: {translator.get_cache_size()} entries")
    print("=" * 60)


if __name__ == "__main__":
    # Run pytest if available
    try:
        pytest.main([__file__, "-v", "-s"])
    except:
        # Fallback to manual tests
        print("Pytest not available, running manual tests...")
        run_manual_tests()
