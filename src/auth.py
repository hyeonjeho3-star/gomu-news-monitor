"""
Authentication Module

This module handles login authentication for gomuhouchi.com premium content.
Features:
- Automatic login form detection
- Session cookie management
- Login validation
- Auto-retry on failure
"""

import logging
import time
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication failures."""
    pass


class Authenticator:
    """
    Handles website authentication and session management.

    Attributes:
        config: Configuration object
        driver: Selenium WebDriver instance
        session_file (Path): Path to saved session cookies
        is_authenticated (bool): Current authentication status
    """

    def __init__(self, config, driver: webdriver.Chrome):
        """
        Initialize authenticator.

        Args:
            config: Configuration object with login credentials
            driver: Selenium WebDriver instance

        Raises:
            ValueError: If login credentials are missing
        """
        self.config = config
        self.driver = driver
        self.session_file = Path("data/session.pkl")
        self.is_authenticated = False

        # Validate credentials
        if not self.config.login_email or not self.config.login_password:
            logger.warning("Login credentials not configured")

    def login(self, max_retries: int = 3) -> bool:
        """
        Perform login to the website.

        Args:
            max_retries: Maximum number of login attempts

        Returns:
            bool: True if login successful, False otherwise

        Raises:
            AuthenticationError: If login fails after all retries

        Example:
            >>> auth = Authenticator(config, driver)
            >>> if auth.login():
            ...     print("Login successful")
        """
        # Check if we have valid session cookies
        if self._load_session():
            logger.info("Restored session from cookies")
            if self._validate_session():
                self.is_authenticated = True
                return True
            else:
                logger.info("Saved session invalid, performing fresh login")

        # Perform fresh login
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Login attempt {attempt}/{max_retries}")
                self._perform_login()

                if self._validate_session():
                    self._save_session()
                    self.is_authenticated = True
                    logger.info("Login successful")
                    return True
                else:
                    logger.warning(f"Login validation failed on attempt {attempt}")

            except Exception as e:
                logger.error(f"Login attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff

        raise AuthenticationError(f"Login failed after {max_retries} attempts")

    def _perform_login(self) -> None:
        """
        Execute the login process.

        This method navigates to the login page, fills in credentials,
        and submits the form.

        Raises:
            TimeoutException: If login page elements not found
            NoSuchElementException: If form fields not found
        """
        try:
            # Navigate to login page
            login_url = self.config.login_url
            logger.debug(f"Navigating to login page: {login_url}")
            self.driver.get(login_url)

            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)

            # Try to find login form elements
            # Method 1: Using configured selectors
            try:
                email_field = wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        self.config.get('site.login_form_selectors.email_field', 'input[type="email"]')
                    ))
                )
                password_field = self.driver.find_element(
                    By.CSS_SELECTOR,
                    self.config.get('site.login_form_selectors.password_field', 'input[type="password"]')
                )

            # Method 2: Fallback to common field names
            except (TimeoutException, NoSuchElementException):
                logger.debug("Trying fallback selectors for login form")
                email_field = self._find_email_field()
                password_field = self._find_password_field()

            # Fill in credentials
            logger.debug("Filling in login credentials")
            email_field.clear()
            email_field.send_keys(self.config.login_email)

            password_field.clear()
            password_field.send_keys(self.config.login_password)

            # Find and click submit button
            submit_button = self._find_submit_button()
            logger.debug("Submitting login form")
            submit_button.click()

            # Wait for navigation after login
            time.sleep(3)

        except Exception as e:
            logger.error(f"Error during login process: {e}")
            raise

    def _find_email_field(self):
        """
        Find email input field using multiple strategies.

        Returns:
            WebElement: Email input field

        Raises:
            NoSuchElementException: If email field not found
        """
        selectors = [
            # gomuhouchi.com specific (SWPM plugin)
            'input[name="swpm_user_name"]',
            'input[id="swpm_user_name"]',
            # Common selectors
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            'input[id="email"]',
            'input[id="username"]',
            'input[placeholder*="メール"]',  # Japanese "email"
        ]

        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                logger.debug(f"Found email field with selector: {selector}")
                return element
            except NoSuchElementException:
                continue

        raise NoSuchElementException("Could not find email input field")

    def _find_password_field(self):
        """
        Find password input field using multiple strategies.

        Returns:
            WebElement: Password input field

        Raises:
            NoSuchElementException: If password field not found
        """
        selectors = [
            # gomuhouchi.com specific (SWPM plugin)
            'input[name="swpm_password"]',
            'input[id="swpm_password"]',
            # Common selectors
            'input[type="password"]',
            'input[name="password"]',
            'input[id="password"]',
            'input[placeholder*="パスワード"]',  # Japanese "password"
        ]

        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                logger.debug(f"Found password field with selector: {selector}")
                return element
            except NoSuchElementException:
                continue

        raise NoSuchElementException("Could not find password input field")

    def _find_submit_button(self):
        """
        Find login submit button using multiple strategies.

        Returns:
            WebElement: Submit button

        Raises:
            NoSuchElementException: If submit button not found
        """
        selectors = [
            # gomuhouchi.com specific (SWPM plugin)
            'input[name="swpm-login"]',
            'input[type="submit"][name="swpm-login"]',
            '.swpm-login-form-submit',
            # Common selectors
            'button[type="submit"]',
            'input[type="submit"]',
            'button:contains("ログイン")',  # Japanese "login"
            'button:contains("Login")',
            'a.login-button',
        ]

        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                logger.debug(f"Found submit button with selector: {selector}")
                return element
            except NoSuchElementException:
                continue

        # Fallback: Find any button or submit input
        try:
            return self.driver.find_element(By.TAG_NAME, 'button')
        except NoSuchElementException:
            pass

        raise NoSuchElementException("Could not find submit button")

    def _validate_session(self) -> bool:
        """
        Validate that the current session is authenticated.

        This checks for indicators that the user is logged in, such as:
        - Presence of logout button
        - User menu/profile elements
        - Absence of login form

        Returns:
            bool: True if session is valid, False otherwise
        """
        try:
            # Check if we're still on login page (bad sign)
            if "login" in self.driver.current_url.lower():
                logger.debug("Still on login page after login attempt")
                return False

            # Check for common logged-in indicators
            logged_in_indicators = [
                'a[href*="logout"]',
                'button:contains("ログアウト")',  # Japanese "logout"
                '.user-menu',
                '.profile-menu',
                '#user-profile',
            ]

            for selector in logged_in_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found logged-in indicator: {selector}")
                    return True
                except NoSuchElementException:
                    continue

            # If no indicators found, assume success if not on login page
            logger.debug("No explicit logged-in indicators found, assuming success")
            return True

        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False

    def _save_session(self) -> None:
        """
        Save current session cookies to file for reuse.

        This allows the session to be restored without logging in again.
        """
        try:
            cookies = self.driver.get_cookies()
            self.session_file.parent.mkdir(parents=True, exist_ok=True)

            session_data = {
                'cookies': cookies,
                'timestamp': datetime.now(),
                'url': self.driver.current_url
            }

            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)

            logger.info(f"Session saved to {self.session_file}")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def _load_session(self) -> bool:
        """
        Load previously saved session cookies.

        Returns:
            bool: True if session loaded successfully, False otherwise
        """
        if not self.session_file.exists():
            logger.debug("No saved session file found")
            return False

        try:
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)

            # Check if session is not too old (24 hours by default)
            session_age = datetime.now() - session_data['timestamp']
            max_age = timedelta(hours=self.config.get('scraping.session_cookie_lifetime_hours', 24))

            if session_age > max_age:
                logger.info(f"Saved session expired ({session_age.total_seconds() / 3600:.1f}h old)")
                return False

            # Navigate to the site first
            self.driver.get(self.config.site_url)
            time.sleep(1)

            # Load cookies
            for cookie in session_data['cookies']:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Could not add cookie: {e}")

            logger.info("Session cookies loaded")
            return True

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    def logout(self) -> None:
        """
        Log out from the website and clear session.

        Example:
            >>> auth.logout()
        """
        try:
            # Try to find and click logout button
            logout_selectors = [
                'a[href*="logout"]',
                'button:contains("ログアウト")',
                '.logout-button',
            ]

            for selector in logout_selectors:
                try:
                    logout_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logout_btn.click()
                    logger.info("Logged out successfully")
                    break
                except NoSuchElementException:
                    continue

        except Exception as e:
            logger.warning(f"Logout attempt failed: {e}")

        finally:
            # Clear session file
            if self.session_file.exists():
                self.session_file.unlink()
                logger.debug("Session file deleted")

            self.is_authenticated = False

    def debug_login_page(self, output_dir: str = ".") -> Dict[str, Any]:
        """
        Analyze login page HTML structure for debugging.

        This method helps identify the correct CSS selectors for login form elements.

        Args:
            output_dir: Directory to save debug output files

        Returns:
            Dictionary containing debug information

        Example:
            >>> auth = Authenticator(config, driver)
            >>> debug_info = auth.debug_login_page()
            >>> print(debug_info['input_fields'])
        """
        from pathlib import Path

        debug_info = {
            'url': self.config.login_url,
            'input_fields': [],
            'buttons': [],
            'submit_buttons': [],
            'links': [],
            'forms': []
        }

        try:
            logger.info(f"Navigating to login page: {self.config.login_url}")
            self.driver.get(self.config.login_url)
            time.sleep(2)  # Wait for page to load

            # Find all input fields
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"Found {len(inputs)} input fields")

            for inp in inputs:
                field_info = {
                    'type': inp.get_attribute('type'),
                    'name': inp.get_attribute('name'),
                    'id': inp.get_attribute('id'),
                    'class': inp.get_attribute('class'),
                    'placeholder': inp.get_attribute('placeholder'),
                    'value': inp.get_attribute('value')
                }
                debug_info['input_fields'].append(field_info)

                print(f"Input: type={field_info['type']}, "
                      f"name={field_info['name']}, "
                      f"id={field_info['id']}, "
                      f"class={field_info['class']}, "
                      f"placeholder={field_info['placeholder']}")

            # Find all buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(f"Found {len(buttons)} buttons")

            for btn in buttons:
                button_info = {
                    'type': btn.get_attribute('type'),
                    'name': btn.get_attribute('name'),
                    'id': btn.get_attribute('id'),
                    'class': btn.get_attribute('class'),
                    'text': btn.text
                }
                debug_info['buttons'].append(button_info)

                print(f"Button: type={button_info['type']}, "
                      f"name={button_info['name']}, "
                      f"id={button_info['id']}, "
                      f"text={button_info['text']}")

            # Find submit inputs
            submits = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
            logger.info(f"Found {len(submits)} submit inputs")

            for sub in submits:
                submit_info = {
                    'name': sub.get_attribute('name'),
                    'id': sub.get_attribute('id'),
                    'value': sub.get_attribute('value'),
                    'class': sub.get_attribute('class')
                }
                debug_info['submit_buttons'].append(submit_info)

                print(f"Submit: name={submit_info['name']}, "
                      f"id={submit_info['id']}, "
                      f"value={submit_info['value']}")

            # Find forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            logger.info(f"Found {len(forms)} forms")

            for form in forms:
                form_info = {
                    'action': form.get_attribute('action'),
                    'method': form.get_attribute('method'),
                    'id': form.get_attribute('id'),
                    'class': form.get_attribute('class')
                }
                debug_info['forms'].append(form_info)

                print(f"Form: action={form_info['action']}, "
                      f"method={form_info['method']}, "
                      f"id={form_info['id']}")

            # Save full HTML
            output_path = Path(output_dir) / "login_page_debug.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

            logger.info(f"HTML saved to: {output_path}")
            print(f"\n✓ Full HTML saved to: {output_path}")

            # Save debug info as JSON
            import json
            json_path = Path(output_dir) / "login_debug_info.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(debug_info, f, indent=2, ensure_ascii=False)

            logger.info(f"Debug info saved to: {json_path}")
            print(f"✓ Debug info saved to: {json_path}")

            # Take screenshot
            screenshot_path = Path(output_dir) / "login_page_screenshot.png"
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"Screenshot saved to: {screenshot_path}")
            print(f"✓ Screenshot saved to: {screenshot_path}")

            return debug_info

        except Exception as e:
            logger.error(f"Error during login page debug: {e}")
            print(f"✗ Error: {e}")
            raise

    def __repr__(self) -> str:
        """String representation of Authenticator object."""
        return f"Authenticator(authenticated={self.is_authenticated})"


if __name__ == "__main__":
    # Test authentication (requires valid credentials in .env)
    from .config import Config

    print("Testing authentication module...")
    print("Note: This requires valid credentials in .env file")
