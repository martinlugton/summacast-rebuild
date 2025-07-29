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
        mock_process.communicate.return_value = ("This is a test summary.", "")
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
        # Calculate expected target_words based on the dummy content
        dummy_content = "This is a dummy transcription content."
        expected_target_words = max(50, len(dummy_content.split()) // 10)

        full_prompt = f"""Produce a summary of the key points in this podcast transcript. The summary should be approximately {expected_target_words} words. Ignore episode credits and advertising in this summary. Once you have done this, please then highlight a key quote from the episode, under the heading '<h3>Key Quote</h3>'. Once you have done that, please list some limitations of the arguments made in the transcript, and potential divergent viewpoints, under the heading '<h3>Potential Limitations and Divergent Views</h3>'. Limit this section to a maximum of 250 words, and a maximum of 4 points.\n\nThis is a dummy transcription content.\n\nSummary:"""
        mock_popen.assert_called_once_with(["cmd.exe", "/c", "gemini", "--model", "gemini-1.5-flash"], stdin=-1, stdout=-1, stderr=-1, text=True, encoding='utf-8')
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
