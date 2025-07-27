import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys

# Add the parent directory to the sys.path to allow importing transcribe_podcast
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transcribe_podcast import transcribe_audio

class TestTranscribePodcast(unittest.TestCase):

    @patch('transcribe_podcast.whisper.load_model')
    @patch('builtins.open', new_callable=mock_open)
    @patch('transcribe_podcast.os.path.splitext')
    @patch('transcribe_podcast.os.path.exists', return_value=True) # Assume audio file exists for transcription test
    def test_transcribe_audio_success(self, mock_exists, mock_splitext, mock_open, mock_load_model):
        mock_audio_path = "/path/to/mock_audio.mp3"
        mock_transcription_text = "This is a test transcription."
        mock_splitext.return_value = ("/path/to/mock_audio", ".mp3")

        # Mock the Whisper model and its transcribe method
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": mock_transcription_text}
        mock_load_model.return_value = mock_model

        result = transcribe_audio(mock_audio_path)

        # Assertions
        mock_load_model.assert_called_once_with("medium", device="cuda")
        mock_model.transcribe.assert_called_once_with(mock_audio_path)

        # Verify transcription file was opened and written to
        expected_transcription_filepath = "/path/to/mock_audio.txt"
        mock_open.assert_called_once_with(expected_transcription_filepath, "w", encoding="utf-8")
        mock_open().write.assert_called_once_with(mock_transcription_text)
        self.assertEqual(result, expected_transcription_filepath)

    @patch('transcribe_podcast.whisper.load_model', side_effect=Exception("Whisper error"))
    @patch('builtins.open', new_callable=mock_open)
    @patch('transcribe_podcast.os.path.splitext')
    @patch('transcribe_podcast.os.path.exists', return_value=True)
    def test_transcribe_audio_error_handling(self, mock_exists, mock_splitext, mock_open, mock_load_model):
        mock_audio_path = "/path/to/mock_audio.mp3"
        mock_splitext.return_value = ("/path/to/mock_audio", ".mp3")

        # Capture print output to check error message
        with patch('builtins.print') as mock_print:
            result = transcribe_audio(mock_audio_path)
            mock_print.assert_any_call(f"An error occurred during transcription: Whisper error")

        mock_open.assert_not_called() # No file should be written on error
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
