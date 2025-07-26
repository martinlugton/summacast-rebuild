import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys

# Add the parent directory to the sys.path to allow importing download_podcast
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from download_podcast import download_latest_podcast_episode, transcribe_podcast_episode

class TestDownloadPodcast(unittest.TestCase):

    @patch('download_podcast.feedparser.parse')
    @patch('download_podcast.requests.get')
    @patch('download_podcast.os.path.exists')
    @patch('download_podcast.os.makedirs')
    @patch('download_podcast.transcribe_podcast_episode') # Mock the transcription function
    def test_download_latest_podcast_episode_success(self, mock_transcribe_podcast_episode, mock_makedirs, mock_exists, mock_requests_get, mock_feedparser_parse):
        # Mock feedparser.parse to return a sample feed
        mock_entry = MagicMock()
        mock_entry.title = 'Test Episode: The Best One!'
        mock_link = MagicMock()
        mock_link.href = 'http://example.com/audio/test_episode.mp3?param=123'
        mock_link.type = 'audio/mpeg'
        mock_link.__contains__.return_value = True # Mock 'type' in link
        mock_entry.links = [mock_link]
        mock_feedparser_parse.return_value.entries = [mock_entry]

        # Mock requests.get to return a dummy response
        mock_response = mock_requests_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b'audio_data_chunk_1', b'audio_data_chunk_2']

        # Mock os.path.exists to indicate the directory does not exist initially, and then the file does not exist
        mock_exists.side_effect = [False, False]

        # Mock open for writing the file
        with patch('builtins.open', mock_open()) as mocked_file:
            expected_filepath = os.path.join("test_podcasts", "Test Episode The Best One.mp3")
            download_latest_podcast_episode("http://example.com/rss_feed.xml", "test_podcasts")

            # Assertions for download
            mock_feedparser_parse.assert_called_once_with("http://example.com/rss_feed.xml")
            mock_exists.assert_any_call("test_podcasts")
            mock_exists.assert_any_call(expected_filepath)
            self.assertEqual(mock_exists.call_count, 2)
            mock_makedirs.assert_called_once_with("test_podcasts")
            mock_requests_get.assert_called_once_with("http://example.com/audio/test_episode.mp3?param=123", stream=True)

            # Check if the file was opened for writing with the correct path and mode
            mocked_file.assert_called_once_with(expected_filepath, 'wb')

            # Check if content was written to the file
            mocked_file().write.assert_any_call(b'audio_data_chunk_1')
            mocked_file().write.assert_any_call(b'audio_data_chunk_2')
            self.assertEqual(mocked_file().write.call_count, 2)

            # Assert that transcribe_podcast_episode was called
            mock_transcribe_podcast_episode.assert_called_once_with(expected_filepath)

    @patch('download_podcast.feedparser.parse')
    @patch('download_podcast.requests.get')
    @patch('download_podcast.os.path.exists')
    @patch('download_podcast.os.makedirs')
    @patch('download_podcast.transcribe_podcast_episode')
    def test_download_latest_podcast_episode_no_episodes(self, mock_transcribe_podcast_episode, mock_makedirs, mock_exists, mock_requests_get, mock_feedparser_parse):
        # Mock feedparser.parse to return an empty feed
        mock_feedparser_parse.return_value.entries = []

        download_latest_podcast_episode("http://example.com/empty_feed.xml", "test_podcasts")

        # Assertions
        mock_feedparser_parse.assert_called_once_with("http://example.com/empty_feed.xml")
        mock_requests_get.assert_not_called()
        mock_exists.assert_not_called() # No directory operations if no episodes
        mock_makedirs.assert_not_called()
        mock_transcribe_podcast_episode.assert_not_called() # Should not transcribe if no episode

    @patch('download_podcast.feedparser.parse')
    @patch('download_podcast.requests.get')
    @patch('download_podcast.os.path.exists')
    @patch('download_podcast.os.makedirs')
    @patch('download_podcast.transcribe_podcast_episode')
    def test_download_latest_podcast_episode_no_audio_enclosure(self, mock_transcribe_podcast_episode, mock_makedirs, mock_exists, mock_requests_get, mock_feedparser_parse):
        # Mock feedparser.parse to return an episode without an audio enclosure
        mock_entry = MagicMock()
        mock_entry.title = 'Episode without audio'
        mock_link = MagicMock()
        mock_link.href = 'http://example.com/text_link.html'
        mock_link.type = 'text/html'
        mock_link.__contains__.return_value = True # Mock 'type' in link
        mock_entry.links = [mock_link]
        mock_feedparser_parse.return_value.entries = [mock_entry]

        download_latest_podcast_episode("http://example.com/no_audio_feed.xml", "test_podcasts")

        # Assertions
        mock_feedparser_parse.assert_called_once_with("http://example.com/no_audio_feed.xml")
        mock_requests_get.assert_not_called()
        mock_exists.assert_not_called()
        mock_makedirs.assert_not_called()
        mock_transcribe_podcast_episode.assert_not_called() # Should not transcribe if no audio

    @patch('download_podcast.transcribe_podcast_episode') # Mock the transcription function
    def test_download_latest_podcast_episode_file_exists(self, mock_transcribe_podcast_episode):
        # This test specifically checks the behavior when the file already exists
        with patch('download_podcast.feedparser.parse') as mock_feedparser_parse, \
             patch('download_podcast.requests.get') as mock_requests_get, \
             patch('download_podcast.os.path.exists') as mock_exists, \
             patch('download_podcast.os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mocked_file:

            # Mock os.path.exists to indicate the directory exists, and then the file exists
            mock_exists.side_effect = [True, True]

            mock_entry = MagicMock()
            mock_entry.title = 'Existing Episode'
            mock_link = MagicMock()
            mock_link.href = 'http://example.com/audio/existing_episode.mp3'
            mock_link.type = 'audio/mpeg'
            mock_link.__contains__.return_value = True
            mock_entry.links = [mock_link]
            mock_feedparser_parse.return_value.entries = [mock_entry]

            download_latest_podcast_episode("http://example.com/existing_feed.xml", "test_podcasts")

            # Assertions
            expected_filepath = os.path.join("test_podcasts", "Existing Episode.mp3")
            mock_feedparser_parse.assert_called_once_with("http://example.com/existing_feed.xml")
            mock_exists.assert_any_call("test_podcasts")
            mock_exists.assert_any_call(expected_filepath)
            self.assertEqual(mock_exists.call_count, 2)
            mock_requests_get.assert_not_called() # Should not download if file exists
            mock_makedirs.assert_not_called()
            mocked_file.assert_not_called()
            mock_transcribe_podcast_episode.assert_called_once_with(expected_filepath)

    def test_filename_sanitization(self):
        # This test directly calls the function with a mocked environment to isolate filename sanitization
        # We need to mock os.path.join and os.path.splitext to control their behavior for this specific test
        with patch('download_podcast.os.path.join', return_value='mocked_path') as mock_join, \
             patch('download_podcast.os.path.splitext', return_value=('episode_with_query', '.mp3')) as mock_splitext, \
             patch('download_podcast.feedparser.parse') as mock_feedparser_parse, \
             patch('download_podcast.requests.get') as mock_requests_get, \
             patch('download_podcast.os.path.exists', return_value=True) as mock_exists, \
             patch('download_podcast.os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mocked_file, \
             patch('download_podcast.transcribe_podcast_episode') as mock_transcribe_podcast_episode: # Mock transcription

            mock_entry = MagicMock()
            mock_entry.title = 'Episode with invalid chars: < > " / \\ | ? *'
            mock_link = MagicMock()
            mock_link.href = 'http://example.com/audio/episode_with_query.mp3?param=value'
            mock_link.type = 'audio/mpeg'
            mock_link.__contains__.return_value = True # Mock 'type' in link
            mock_entry.links = [mock_link]
            mock_feedparser_parse.return_value.entries = [mock_entry]
            mock_response = mock_requests_get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [b'dummy_data']

            download_latest_podcast_episode("http://example.com/test_feed.xml", "test_dir")

            # The sanitized filename should be 'Episode with invalid chars - .mp3'
            # The regex replaces invalid characters with an empty string, so spaces remain.
            # The strip() removes leading/trailing whitespace.
            expected_filename_part = "Episode with invalid chars"
            expected_extension = ".mp3"

            # Check the call to os.path.join to see the sanitized filename
            # The second argument to os.path.join is the filename
            self.assertIn(expected_filename_part, mock_join.call_args[0][1])
            self.assertTrue(mock_join.call_args[0][1].endswith(expected_extension))

    @patch('download_podcast.whisper.load_model')
    @patch('builtins.open', new_callable=mock_open)
    @patch('download_podcast.os.path.splitext')
    @patch('download_podcast.os.path.exists', return_value=True) # Assume audio file exists for transcription test
    def test_transcribe_podcast_episode_success(self, mock_exists, mock_splitext, mock_open, mock_load_model):
        mock_audio_path = "/path/to/mock_audio.mp3"
        mock_transcription_text = "This is a test transcription."
        mock_splitext.return_value = ("/path/to/mock_audio", ".mp3")

        # Mock the Whisper model and its transcribe method
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": mock_transcription_text}
        mock_load_model.return_value = mock_model

        transcribe_podcast_episode(mock_audio_path)

        # Assertions
        mock_load_model.assert_called_once_with("medium", device="cuda")
        mock_model.transcribe.assert_called_once_with(mock_audio_path)

        # Verify transcription file was opened and written to
        expected_transcription_filepath = "/path/to/mock_audio.txt"
        expected_summary_filepath = "/path/to/mock_audio.summary.txt"
        mock_open.assert_any_call(expected_transcription_filepath, "w", encoding="utf-8")
        mock_open.assert_any_call(expected_transcription_filepath, "r", encoding="utf-8") # For summarization
        mock_open.assert_any_call(expected_summary_filepath, "w", encoding="utf-8") # For summarization
        mock_open().write.assert_any_call(mock_transcription_text)

    @patch('download_podcast.whisper.load_model', side_effect=Exception("Whisper error"))
    @patch('builtins.open', new_callable=mock_open)
    @patch('download_podcast.os.path.splitext')
    @patch('download_podcast.os.path.exists', return_value=True)
    def test_transcribe_podcast_episode_error_handling(self, mock_exists, mock_splitext, mock_open, mock_load_model):
        mock_audio_path = "/path/to/mock_audio.mp3"
        mock_splitext.return_value = ("/path/to/mock_audio", ".mp3")

        # Capture print output to check error message
        with patch('builtins.print') as mock_print:
            transcribe_podcast_episode(mock_audio_path)
            mock_print.assert_any_call(f"An error occurred during transcription: Whisper error")

        mock_open.assert_not_called() # No file should be written on error

if __name__ == '__main__':
    unittest.main()