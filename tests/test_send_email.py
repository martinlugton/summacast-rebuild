import unittest
import os
from unittest.mock import patch
import sys
import logging

# Add the parent directory to the sys.path to allow importing send_email
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from send_email import send_email
from app import app # Import the app for context

class TestSendEmail(unittest.TestCase):

    def setUp(self):
        # Set up mock environment variables for testing
        os.environ["AHASEND_API_KEY"] = "test_api_key"
        os.environ["SENDER_EMAIL"] = "test@example.com"
        os.environ["RECIPIENT_EMAIL"] = "recipient@example.com"
        # Disable logging during tests to prevent clutter
        logging.disable(logging.CRITICAL)
        # Push an application context
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Clean up environment variables after testing
        for var in ["AHASEND_API_KEY", "SENDER_EMAIL", "RECIPIENT_EMAIL"]:
            if var in os.environ:
                del os.environ[var]
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)
        # Pop the application context
        self.app_context.pop()

    @patch('send_email.render_template')
    @patch('send_email.markdown.markdown')
    @patch('requests.post')
    def test_send_email_success(self, mock_post, mock_markdown, mock_render_template):
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {'success_count': 1}
        mock_markdown.return_value = "markdown_summary"
        mock_render_template.return_value = "<html><body>markdown_summary</body></html>"

        result = send_email(
            "Test Subject",
            "Test Text Body", # This argument is unused
            "Test Summary Content",
            "Test Podcast",
            "Test Episode",
            "2025-01-01"
        )

        mock_markdown.assert_called_once_with("Test Summary Content")
        mock_render_template.assert_called_once_with(
            'email_summary_template.html',
            podcast_name="Test Podcast",
            episode_title="Test Episode",
            published_date="2025-01-01",
            summary_content="markdown_summary"
        )
        mock_post.assert_called_once_with(
            'https://api.ahasend.com/v1/email/send',
            json={
                'from': {'name': 'Summacast', 'email': 'test@example.com'},
                'recipients': [{'name': 'Podcast Listener', 'email': 'recipient@example.com'}],
                'content': {'subject': 'Test Subject', 'html_body': '<html><body>markdown_summary</body></html>'},
            },
            headers={'X-Api-Key': 'test_api_key', 'Content-Type': 'application/json'}
        )
        self.assertTrue(result)

    @patch('requests.post')
    def test_send_email_missing_env_vars(self, mock_post):
        del os.environ["AHASEND_API_KEY"]
        result = send_email("Test Subject", "Test Text Body", "Test Summary", "Podcast", "Episode", "Date")
        mock_post.assert_not_called()
        self.assertFalse(result)

    @patch('send_email.render_template')
    @patch('send_email.markdown.markdown')
    @patch('requests.post')
    def test_send_email_custom_recipient(self, mock_post, mock_markdown, mock_render_template):
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {'success_count': 1}
        mock_markdown.return_value = "markdown_summary"
        mock_render_template.return_value = "<html><body>markdown_summary</body></html>"

        result = send_email(
            "Test Subject",
            "Test Text Body",
            "Test Summary Content",
            "Test Podcast",
            "Test Episode",
            "2025-01-01",
            recipient_email="custom@example.com"
        )

        mock_post.assert_called_once_with(
            'https://api.ahasend.com/v1/email/send',
            json={
                'from': {'name': 'Summacast', 'email': 'test@example.com'},
                'recipients': [{'name': 'Podcast Listener', 'email': 'custom@example.com'}],
                'content': {'subject': 'Test Subject', 'html_body': '<html><body>markdown_summary</body></html>'},
            },
            headers={'X-Api-Key': 'test_api_key', 'Content-Type': 'application/json'}
        )
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()