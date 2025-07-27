import unittest
import os
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from send_email import send_email

class TestSendEmail(unittest.TestCase):

    def setUp(self):
        # Set up mock environment variables for testing
        os.environ["AHASEND_API_KEY"] = "test_api_key"
        os.environ["SENDER_EMAIL"] = "test@example.com"
        os.environ["RECIPIENT_EMAIL"] = "recipient@example.com"
        os.environ["SENDER_NAME"] = "Test Sender"

    def tearDown(self):
        # Clean up environment variables after testing
        for var in ["AHASEND_API_KEY", "SENDER_EMAIL", "RECIPIENT_EMAIL", "SENDER_NAME"]:
            if var in os.environ:
                del os.environ[var]

    @patch('requests.post')
    def test_send_email_success(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {'success_count': 1}

        send_email("Test Subject", "Test Text Body", "<p>Test HTML Body</p>")

        mock_post.assert_called_once_with(
            'https://api.ahasend.com/v1/email/send',
            json={
                'from': {'name': 'Summacast', 'email': 'test@example.com'},
                'recipients': [{'name': 'Podcast Listener', 'email': 'recipient@example.com'}],
                'content': {'subject': 'Test Subject', 'text_body': 'Test Text Body', 'html_body': '<p>Test HTML Body</p>'},
            },
            headers={'X-Api-Key': 'test_api_key', 'Content-Type': 'application/json'}
        )

    @patch('requests.post')
    def test_send_email_missing_env_vars(self, mock_post):
        del os.environ["AHASEND_API_KEY"]
        send_email("Test Subject", "Test Text Body", "<p>Test HTML Body</p>")
        mock_post.assert_not_called()

if __name__ == '__main__':
    unittest.main()
