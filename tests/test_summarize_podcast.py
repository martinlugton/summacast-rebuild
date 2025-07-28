import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import subprocess
import logging

# Add the parent directory to the sys.path to allow importing summarize_podcast
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from summarize_podcast import summarize_text

class TestSummarizePodcast(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_summaries"
        os.makedirs(self.test_dir, exist_ok=True)
        self.dummy_transcription_path = os.path.join(self.test_dir, "dummy_transcription.txt")
        self.expected_summary_path = os.path.join(self.test_dir, "dummy_transcription.summary.txt")
        # Disable logging during tests to prevent clutter
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        if os.path.exists(self.dummy_transcription_path):
            os.remove(self.dummy_transcription_path)
        if os.path.exists(self.expected_summary_path):
            os.remove(self.expected_summary_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)

    @patch('subprocess.Popen')
    def test_summarize_text_success(self, mock_popen):
        # Mock subprocess.Popen to simulate Gemini CLI output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("""Loaded cached credentials.\nThis is a test summary.\n""", "")
        mock_popen.return_value = mock_process

        # Create a dummy transcription file
        with open(self.dummy_transcription_path, "w", encoding="utf-8") as f:
            f.write("This is a dummy transcription content.")

        # Call the summarize_text function
        summary = summarize_text(self.dummy_transcription_path)

        # Assertions
        self.assertIsNotNone(summary)
        self.assertEqual(summary, "This is a test summary.")
        self.assertTrue(os.path.exists(self.expected_summary_path))

        with open(self.expected_summary_path, "r", encoding="utf-8") as f:
            saved_summary = f.read()
        self.assertEqual(saved_summary, "This is a test summary.")

        # Verify subprocess.Popen was called correctly with the prompt
        expected_prompt_part = "Please summarize the following podcast transcript to approximately 10% of its original length:"
        full_prompt = f"{expected_prompt_part}\n\nThis is a dummy transcription content.\n\nSummary:"
        mock_popen.assert_called_once()
        mock_process.communicate.assert_called_once_with(input=full_prompt)

    @patch('subprocess.Popen')
    def test_summarize_text_cli_error(self, mock_popen):
        # Mock subprocess.Popen to simulate a CLI error
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "CLI Error Message")
        mock_popen.return_value = mock_process

        # Create a dummy transcription file
        with open(self.dummy_transcription_path, "w", encoding="utf-8") as f:
            f.write("This is a dummy transcription content.")

        # Capture logging output to check error message
        with patch('summarize_podcast.logger.error') as mock_logger_error:
            # Call the summarize_text function and expect it to return None due to error
            summary = summarize_text(self.dummy_transcription_path)
            mock_logger_error.assert_called_once_with(
                f"Gemini CLI command failed with exit code 1.\nStdout: \nStderr: CLI Error Message"
            )

        # Assertions
        self.assertIsNone(summary)
        self.assertFalse(os.path.exists(self.expected_summary_path)) # Summary file should not be created

if __name__ == '__main__':
    unittest.main()
