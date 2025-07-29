import unittest
import os
from unittest.mock import patch
import sys
import logging
import requests

# Add the parent directory to the sys.path to allow importing send_email
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from send_email import send_email

class TestSendEmail(unittest.TestCase):

    def setUp(self):
        # Set up mock environment variables for testing
        os.environ["AHASEND_API_KEY"] = "test_api_key"
        os.environ["SENDER_EMAIL"] = "test@example.com"
        os.environ["RECIPIENT_EMAIL"] = "recipient@example.com"
        # Disable logging during tests to prevent clutter
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Clean up environment variables after testing
        for var in ["AHASEND_API_KEY", "SENDER_EMAIL", "RECIPIENT_EMAIL"]:
            if var in os.environ:
                del os.environ[var]
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)

    @patch('requests.post')
    def test_send_email_success(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {'success_count': 1}

        result = send_email("Test Subject", "Test Text Body", "<p>Test HTML Body</p>")

        mock_post.assert_called_once_with(
            'https://api.ahasend.com/v1/email/send',
            json={
                'from': {'name': 'Summacast', 'email': 'test@example.com'},
                'recipients': [{'name': 'Podcast Listener', 'email': 'recipient@example.com'}],
                'content': {'subject': 'Test Subject', 'text_body': 'Test Text Body', 'html_body': '<p>Test HTML Body</p>'},
            },
            headers={'X-Api-Key': 'test_api_key', 'Content-Type': 'application/json'}
        )
        self.assertTrue(result)

    @patch('requests.post')
    def test_send_email_missing_env_vars(self, mock_post):
        del os.environ["AHASEND_API_KEY"]
        result = send_email("Test Subject", "Test Text Body", "<p>Test HTML Body</p>")
        mock_post.assert_not_called()
        self.assertFalse(result)

    @patch('requests.post')
    def test_send_email_custom_recipient(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {'success_count': 1}

        result = send_email("Test Subject", "Test Text Body", "<p>Test HTML Body</p>", recipient_email="custom@example.com")

        mock_post.assert_called_once_with(
            'https://api.ahasend.com/v1/email/send',
            json={
                'from': {'name': 'Summacast', 'email': 'test@example.com'},
                'recipients': [{'name': 'Podcast Listener', 'email': 'custom@example.com'}],
                'content': {'subject': 'Test Subject', 'text_body': 'Test Text Body', 'html_body': '<p>Test HTML Body</p>'},
            },
            headers={'X-Api-Key': 'test_api_key', 'Content-Type': 'application/json'}
        )
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
