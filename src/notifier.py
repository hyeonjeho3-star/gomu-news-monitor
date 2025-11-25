"""
Notification Module

This module handles sending notifications via email (and optionally Telegram/Slack).
Features:
- HTML email templates
- Batch notifications
- Retry logic
- Multiple recipient support
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Custom exception for notification failures."""
    pass


class Notifier:
    """
    Handles email and other notifications for new articles.

    Attributes:
        config: Configuration object
    """

    def __init__(self, config):
        """
        Initialize notifier.

        Args:
            config: Configuration object with email settings

        Raises:
            ValueError: If email configuration is missing
        """
        self.config = config

        # Validate email configuration
        if not self.config.email_from or not self.config.email_password:
            logger.warning("Email credentials not configured")

        if not self.config.email_recipients:
            logger.warning("No email recipients configured")

    def send_article_notifications(
        self,
        articles: List[Dict[str, Any]],
        max_retries: int = 3
    ) -> bool:
        """
        Send email notifications for new articles.

        Args:
            articles: List of article dictionaries to notify about
            max_retries: Maximum number of retry attempts

        Returns:
            bool: True if notification sent successfully

        Example:
            >>> notifier = Notifier(config)
            >>> notifier.send_article_notifications(new_articles)
        """
        if not articles:
            logger.info("No articles to notify about")
            return True

        if not self.config.email_recipients:
            logger.error("No email recipients configured")
            return False

        try:
            # Group articles by urgency
            urgent_articles = [a for a in articles if a.get('is_urgent', False)]
            normal_articles = [a for a in articles if not a.get('is_urgent', False)]

            # Send urgent articles immediately
            if urgent_articles:
                logger.info(f"Sending urgent notification for {len(urgent_articles)} articles")
                self._send_email(urgent_articles, is_urgent=True, max_retries=max_retries)

            # Send normal articles (batch if enabled)
            if normal_articles:
                if self.config.batch_notifications:
                    logger.info(f"Sending batch notification for {len(normal_articles)} articles")
                    self._send_email(normal_articles, is_urgent=False, max_retries=max_retries)
                else:
                    logger.info(f"Sending individual notifications for {len(normal_articles)} articles")
                    for article in normal_articles:
                        self._send_email([article], is_urgent=False, max_retries=max_retries)

            return True

        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
            return False

    def _send_email(
        self,
        articles: List[Dict[str, Any]],
        is_urgent: bool = False,
        max_retries: int = 3
    ) -> None:
        """
        Send email notification with retry logic.

        Args:
            articles: List of articles to include in email
            is_urgent: Whether this is an urgent notification
            max_retries: Maximum retry attempts

        Raises:
            NotificationError: If email sending fails after all retries
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Email send attempt {attempt}/{max_retries}")

                # Create email message
                msg = self._create_email_message(articles, is_urgent)

                # Send email
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    if self.config.use_tls:
                        server.starttls()

                    server.login(self.config.email_from, self.config.email_password)

                    for recipient in self.config.email_recipients:
                        server.send_message(msg, to_addrs=[recipient])
                        logger.info(f"Email sent to {recipient}")

                return  # Success

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Email authentication failed: {e}")
                raise NotificationError("Invalid email credentials")

            except smtplib.SMTPException as e:
                logger.warning(f"Email send attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise NotificationError(f"Email sending failed after {max_retries} attempts: {e}")

            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                raise NotificationError(f"Email sending error: {e}")

    def _create_email_message(
        self,
        articles: List[Dict[str, Any]],
        is_urgent: bool = False
    ) -> MIMEMultipart:
        """
        Create formatted email message.

        Args:
            articles: List of articles to include
            is_urgent: Whether this is an urgent notification

        Returns:
            MIMEMultipart email message
        """
        msg = MIMEMultipart('alternative')

        # Subject
        subject_prefix = self.config.get('email.subject_prefix', '[고무뉴스]')
        if is_urgent:
            subject = f"{subject_prefix} 【긴급】새로운 기사 {len(articles)}건 발견"
        else:
            subject = f"{subject_prefix} 새로운 기사 {len(articles)}건 발견"

        msg['Subject'] = subject
        msg['From'] = self.config.email_from
        msg['To'] = ', '.join(self.config.email_recipients)
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

        # Email body (plain text version)
        text_body = self._create_text_body(articles, is_urgent)
        part1 = MIMEText(text_body, 'plain', 'utf-8')

        # Email body (HTML version)
        html_body = self._create_html_body(articles, is_urgent)
        part2 = MIMEText(html_body, 'html', 'utf-8')

        # Attach both versions
        msg.attach(part1)
        msg.attach(part2)

        return msg

    def _create_text_body(
        self,
        articles: List[Dict[str, Any]],
        is_urgent: bool = False
    ) -> str:
        """
        Create plain text email body.

        Args:
            articles: List of articles
            is_urgent: Whether this is urgent

        Returns:
            Plain text email content
        """
        lines = []

        if is_urgent:
            lines.append("=" * 60)
            lines.append("【긴급】새로운 기사가 발견되었습니다!")
            lines.append("=" * 60)
        else:
            lines.append("고무 업계 뉴스 모니터링 알림")
            lines.append("=" * 60)

        # 로그인 정보 추가
        lines.append("")
        lines.append("┌" + "─" * 40 + "┐")
        lines.append("│    🔐 고무호지신문 로그인 정보         │")
        lines.append("│" + "─" * 40 + "│")
        lines.append("│      ID : gomu1239                     │")
        lines.append("│      PW : DRB@12345678                 │")
        lines.append("│                                        │")
        lines.append("│   🌐 https://gomuhouchi.com            │")
        lines.append("└" + "─" * 40 + "┘")
        lines.append("")

        lines.append(f"\n총 {len(articles)}건의 새로운 기사가 발견되었습니다.\n")

        for i, article in enumerate(articles, 1):
            lines.append(f"\n[기사 {i}]")
            lines.append(f"제목: {article['title']}")

            # Add Korean translation if available
            if article.get('title_ko'):
                lines.append(f"번역: {article['title_ko']}")

            lines.append(f"키워드: {article['matched_keyword']}")
            lines.append(f"링크: {article['url']}")

            if article.get('published_date'):
                lines.append(f"게시일: {article['published_date']}")

            if article.get('summary'):
                lines.append(f"요약: {article['summary'][:200]}...")

            lines.append("-" * 60)

        lines.append(f"\n\n모니터링 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n이 메일은 Gomu News Monitor에 의해 자동으로 발송되었습니다.")

        return '\n'.join(lines)

    def _create_html_body(
        self,
        articles: List[Dict[str, Any]],
        is_urgent: bool = False
    ) -> str:
        """
        Create HTML email body with styling.

        Args:
            articles: List of articles
            is_urgent: Whether this is urgent

        Returns:
            HTML email content
        """
        # Color scheme
        urgent_color = "#dc3545"
        normal_color = "#007bff"
        highlight_color = "#ffc107"

        header_color = urgent_color if is_urgent else normal_color

        html_parts = [
            """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {
                        font-family: 'Segoe UI', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .header {
                        background: linear-gradient(135deg, """ + header_color + """ 0%, """ + header_color + """dd 100%);
                        color: white;
                        padding: 30px;
                        border-radius: 10px 10px 0 0;
                        text-align: center;
                    }
                    .header h1 {
                        margin: 0;
                        font-size: 24px;
                    }
                    .summary {
                        background: #f8f9fa;
                        padding: 20px;
                        border-left: 4px solid """ + header_color + """;
                        margin: 20px 0;
                    }
                    .article {
                        background: white;
                        border: 1px solid #dee2e6;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 20px 0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .article-title {
                        color: #212529;
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 10px;
                    }
                    .article-title a {
                        color: """ + header_color + """;
                        text-decoration: none;
                    }
                    .article-title a:hover {
                        text-decoration: underline;
                    }
                    .keyword-badge {
                        background: """ + highlight_color + """;
                        color: #000;
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: bold;
                        display: inline-block;
                        margin: 5px 0;
                    }
                    .article-meta {
                        color: #6c757d;
                        font-size: 14px;
                        margin: 10px 0;
                    }
                    .article-summary {
                        color: #495057;
                        margin: 15px 0;
                        line-height: 1.6;
                    }
                    .footer {
                        text-align: center;
                        color: #6c757d;
                        font-size: 12px;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #dee2e6;
                    }
                    .urgent-badge {
                        background: """ + urgent_color + """;
                        color: white;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                        display: inline-block;
                        margin: 10px 0;
                    }
                    .credentials-box {
                        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
                        border: 3px solid #ffd700;
                        border-radius: 12px;
                        padding: 20px 25px;
                        margin: 20px 0;
                        text-align: center;
                        box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
                    }
                    .credentials-title {
                        color: #ffd700;
                        font-size: 16px;
                        font-weight: bold;
                        margin-bottom: 15px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                    .credentials-content {
                        background: rgba(255, 255, 255, 0.95);
                        border-radius: 8px;
                        padding: 15px 20px;
                        display: inline-block;
                    }
                    .credential-item {
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 18px;
                        font-weight: bold;
                        color: #1a237e;
                        margin: 8px 0;
                        letter-spacing: 0.5px;
                    }
                    .credential-label {
                        color: #e53935;
                        font-weight: bold;
                        display: inline-block;
                        min-width: 45px;
                    }
                    .credential-value {
                        color: #1565c0;
                        background: #e3f2fd;
                        padding: 4px 10px;
                        border-radius: 4px;
                        margin-left: 8px;
                    }
                    .credentials-link {
                        color: #ffd700;
                        font-size: 13px;
                        margin-top: 12px;
                    }
                    .credentials-link a {
                        color: #ffd700;
                        text-decoration: underline;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🔔 고무 업계 뉴스 알림</h1>
            """
        ]

        if is_urgent:
            html_parts.append('<div class="urgent-badge">⚠️ 긴급 알림</div>')

        html_parts.append('</div>')

        # Credentials box (로그인 정보)
        html_parts.append("""
            <div class="credentials-box">
                <div class="credentials-title">🔐 고무호지신문 로그인 정보</div>
                <div class="credentials-content">
                    <div class="credential-item">
                        <span class="credential-label">ID :</span>
                        <span class="credential-value">gomu1239</span>
                    </div>
                    <div class="credential-item">
                        <span class="credential-label">PW :</span>
                        <span class="credential-value">DRB@12345678</span>
                    </div>
                </div>
                <div class="credentials-link">
                    🌐 <a href="https://gomuhouchi.com" target="_blank">고무호지신문 바로가기</a>
                </div>
            </div>
        """)

        # Summary section
        html_parts.append(f"""
            <div class="summary">
                <strong>총 {len(articles)}건의 새로운 기사가 발견되었습니다.</strong><br>
                모니터링 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
            </div>
        """)

        # Articles
        for i, article in enumerate(articles, 1):
            html_parts.append(f"""
                <div class="article">
                    <div class="article-title">
                        {i}. <a href="{article['url']}" target="_blank">{article['title']}</a>
                    </div>
            """)

            # Add Korean translation if available
            if article.get('title_ko'):
                html_parts.append(f"""
                    <div style="margin: 8px 0 15px 0; padding-left: 15px; border-left: 3px solid #4CAF50; color: #2c5f2d; font-size: 15px; line-height: 1.6; font-weight: 500;">
                        → {article['title_ko']}
                    </div>
                """)

            html_parts.append("""
                    <div>
                        <span class="keyword-badge">🔑 """ + article['matched_keyword'] + """</span>
            """)

            if article.get('is_urgent'):
                html_parts.append('<span class="urgent-badge">긴급</span>')

            html_parts.append('</div>')

            if article.get('published_date'):
                html_parts.append(f"""
                    <div class="article-meta">
                        📅 게시일: {article['published_date']}
                    </div>
                """)

            if article.get('summary'):
                summary = article['summary'][:300]
                if len(article['summary']) > 300:
                    summary += '...'
                html_parts.append(f"""
                    <div class="article-summary">
                        {summary}
                    </div>
                """)

            html_parts.append(f"""
                <div class="article-meta">
                    🔗 <a href="{article['url']}" target="_blank">기사 전문 보기</a>
                </div>
            </div>
            """)

        # Footer
        html_parts.append("""
            <div class="footer">
                <p>이 메일은 <strong>Gomu News Monitor</strong>에 의해 자동으로 발송되었습니다.</p>
                <p>© 2024 Gomu News Monitor. All rights reserved.</p>
            </div>
            </body>
            </html>
        """)

        return ''.join(html_parts)

    def send_error_notification(self, error_message: str) -> None:
        """
        Send error notification to administrators.

        Args:
            error_message: Error message to send

        Example:
            >>> notifier.send_error_notification("Database connection failed")
        """
        if not self.config.get('email.send_error_notifications', True):
            return

        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"{self.config.get('email.subject_prefix', '[고무뉴스]')} 【오류】모니터링 에러 발생"
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_recipients)

            body = f"""
            고무 뉴스 모니터링 시스템에서 오류가 발생했습니다.

            시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            오류 메시지:
            {error_message}

            시스템을 확인해 주세요.

            ---
            Gomu News Monitor
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.email_from, self.config.email_password)
                server.send_message(msg)

            logger.info("Error notification sent")

        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

    def send_test_email(self) -> bool:
        """
        Send test email to verify configuration.

        Returns:
            bool: True if test email sent successfully

        Example:
            >>> if notifier.send_test_email():
            ...     print("Email configuration is working!")
        """
        try:
            test_article = {
                'article_id': 'test-001',
                'title': 'テストメール - Test Email',
                'url': 'https://gomuhouchi.com',
                'matched_keyword': 'テスト',
                'summary': 'これはテストメールです。メール設定が正常に動作しています。',
                'published_date': datetime.now().isoformat(),
                'is_urgent': False
            }

            self._send_email([test_article], is_urgent=False, max_retries=1)
            logger.info("Test email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Test email failed: {e}")
            return False

    def __repr__(self) -> str:
        """String representation of Notifier object."""
        return f"Notifier(recipients={len(self.config.email_recipients)})"


if __name__ == "__main__":
    # Test notifier
    from .config import Config

    print("Testing notifier module...")
    config = Config()

    notifier = Notifier(config)
    print(f"Email recipients: {config.email_recipients}")

    if config.email_from and config.email_recipients:
        print("\nSending test email...")
        if notifier.send_test_email():
            print("✓ Test email sent successfully")
        else:
            print("✗ Test email failed")
    else:
        print("✗ Email not configured")
