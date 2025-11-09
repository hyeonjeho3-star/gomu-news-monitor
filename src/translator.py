"""
Translation Module

This module handles translation of Japanese article titles to Korean.
Features:
- Automatic Japanese to Korean translation
- Translation caching for performance
- Error handling with fallback
- Rate limiting protection
"""

import logging
import time
from typing import Optional, Dict, List
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


class ArticleTranslator:
    """
    Translates Japanese article titles to Korean.

    Features:
    - Automatic language detection
    - Translation caching
    - Error handling with fallback
    - Rate limiting protection
    """

    def __init__(self):
        """Initialize translator with Google Translate (free)."""
        try:
            self.translator = GoogleTranslator(source='ja', target='ko')
            self.cache: Dict[str, str] = {}  # Translation cache
            self.last_request_time = 0.0
            self.min_request_interval = 0.5  # seconds (Rate limit protection)
            logger.info("ArticleTranslator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize translator: {e}")
            self.translator = None
            self.cache = {}

    def translate(self, text: str) -> Optional[str]:
        """
        Translate Japanese text to Korean.

        Args:
            text: Japanese text to translate

        Returns:
            Translated Korean text, or None if translation fails

        Example:
            >>> translator = ArticleTranslator()
            >>> result = translator.translate("バンドー化学")
            >>> print(result)
            "반도화학"
        """
        if not text or not text.strip():
            logger.debug("Empty text provided for translation")
            return None

        if not self.translator:
            logger.warning("Translator not initialized, skipping translation")
            return None

        # Check cache first
        if text in self.cache:
            logger.debug(f"Translation cache hit: {text[:30]}...")
            return self.cache[text]

        try:
            # Rate limiting (prevent too many requests)
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

            # Perform translation
            logger.debug(f"Translating: {text[:50]}...")
            translated = self.translator.translate(text)

            self.last_request_time = time.time()

            # Cache the result
            if translated:
                self.cache[text] = translated
                logger.info(f"Translation success: {text[:30]}... → {translated[:30]}...")
                return translated
            else:
                logger.warning(f"Translation returned empty result for: {text[:50]}...")
                return None

        except Exception as e:
            logger.error(f"Translation failed for '{text[:50]}...': {e}")
            return None

    def translate_batch(self, texts: List[str]) -> Dict[str, Optional[str]]:
        """
        Translate multiple texts.

        Args:
            texts: List of Japanese texts

        Returns:
            Dictionary mapping original text to translated text

        Example:
            >>> translator = ArticleTranslator()
            >>> results = translator.translate_batch(["テスト1", "テスト2"])
            >>> print(results)
            {"テスト1": "테스트1", "テスト2": "테스트2"}
        """
        results = {}
        total = len(texts)

        logger.info(f"Starting batch translation of {total} texts...")

        for index, text in enumerate(texts, 1):
            logger.debug(f"Translating {index}/{total}")
            translated = self.translate(text)
            results[text] = translated

        success_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"Batch translation complete: {success_count}/{total} successful")

        return results

    def clear_cache(self):
        """Clear translation cache."""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"Translation cache cleared ({cache_size} entries)")

    def get_cache_size(self) -> int:
        """Get number of cached translations."""
        return len(self.cache)

    def __repr__(self) -> str:
        """String representation of ArticleTranslator object."""
        return f"ArticleTranslator(cached={len(self.cache)})"


# Module-level singleton instance
_translator_instance: Optional[ArticleTranslator] = None


def get_translator() -> ArticleTranslator:
    """
    Get singleton translator instance.

    Returns:
        ArticleTranslator instance

    Example:
        >>> translator = get_translator()
        >>> result = translator.translate("バンドー化学")
    """
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = ArticleTranslator()
    return _translator_instance


def clear_translator_cache():
    """
    Clear the singleton translator's cache.

    Example:
        >>> clear_translator_cache()
    """
    translator = get_translator()
    translator.clear_cache()


if __name__ == "__main__":
    # Test the translator
    print("Testing ArticleTranslator...")

    translator = get_translator()

    test_texts = [
        "バンドー化学、産業資材事業は増収大幅増益",
        "三ツ星ベルト、寄付金贈呈式とミュージックサロンを開催",
        "テスト",
    ]

    print("\nSingle translations:")
    for text in test_texts:
        result = translator.translate(text)
        print(f"  {text}")
        print(f"  → {result}\n")

    print(f"\nCache size: {translator.get_cache_size()}")

    print("\nBatch translation:")
    results = translator.translate_batch(["新製品", "開発中", "発表"])
    for original, translated in results.items():
        print(f"  {original} → {translated}")
