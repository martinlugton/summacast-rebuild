import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
import logging

# Add the parent directory to the sys.path to allow importing main_workflow
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main_workflow import process_podcasts
import database_manager

DATABASE_NAME = "summacast.db" # Define the database name for cleanup

class TestMainWorkflow(unittest.TestCase):

    def setUp(self):
        # Disable logging during tests to prevent clutter
        logging.disable(logging.CRITICAL)
        # Clean up any existing database file
        if os.path.exists(DATABASE_NAME):
            os.remove(DATABASE_NAME)
        database_manager.create_table()
        database_manager.create_podcast_configs_table()

    def tearDown(self):
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)
        # Clean up any created files and database
        if os.path.exists(DATABASE_NAME):
            os.remove(DATABASE_NAME)
class TestMainWorkflow(unittest.TestCase):

    def setUp(self):
        # Disable logging during tests to prevent clutter
        logging.disable(logging.CRITICAL)
        # Clean up any existing database file
        if os.path.exists(database_manager.DATABASE_NAME):
            os.remove(database_manager.DATABASE_NAME)
        database_manager.create_table()
        database_manager.create_podcast_configs_table()
        database_manager.create_podcast_configs_table()

    def tearDown(self):
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)
        # Clean up any created files and database
        if os.path.exists(database_manager.DATABASE_NAME):
            os.remove(database_manager.DATABASE_NAME)

    @patch('main_workflow.download_latest_podcast_episode')
    @patch('main_workflow.transcribe_audio')
    @patch('main_workflow.summarize_text')
    @patch('main_workflow.send_email')
    @patch('main_workflow.time.sleep')
    @patch('main_workflow.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_workflow_new_episode_processed(self, mock_open_builtin, mock_exists, mock_sleep, mock_send_email, mock_summarize_text, mock_transcribe_audio, mock_download_episode):
        # Mock podcast_config.json content
        mock_exists.side_effect = [True, True, True] # podcast_config.json, processed_episodes.json, then for each episode
        mock_open_builtin.side_effect = [
            mock_open(read_data=json.dumps([
                {"name": "Test Podcast", "rss_feed_url": "http://test.com/rss"}
            ])).return_value, # For podcast_config.json
            mock_open(read_data=json.dumps({})).return_value, # For processed_episodes.json (initial load)
            mock_open().return_value # For processed_episodes.json (save)
        ]

        # Mock download_latest_podcast_episode to return a new episode
        mock_download_episode.return_value = {
            "episode_title": "New Episode",
            "episode_url": "http://test.com/new_episode.mp3",
            "file_path": "podcasts/new_episode.mp3",
            "is_new_download": True,
            "published_date": "2025-07-27T12:00:00"
        }
        mock_transcribe_audio.return_value = "transcription.txt"
        mock_summarize_text.return_value = "This is a summary."
        mock_send_email.return_value = True # Email sent successfully

        # Run main for one iteration
        with patch('database_manager.get_all_podcast_configs') as mock_get_all_podcast_configs:
            with patch('database_manager.episode_exists') as mock_episode_exists:
                with patch('database_manager.add_episode') as mock_add_episode:
                    with patch('main_workflow.time.sleep') as mock_sleep:

                        mock_get_all_podcast_configs.return_value = [
                            {"name": "Test Podcast", "rss_feed_url": "http://test.com/rss", "recipient_email": "test@example.com"}
                        ]
                        mock_episode_exists.return_value = False # Episode does not exist in DB
                        mock_add_episode.return_value = True # Episode added successfully

                        # To stop the infinite loop after one iteration
                        mock_sleep.side_effect = [KeyboardInterrupt]

                        try:
                            process_podcasts()
                        except KeyboardInterrupt:
                            pass

                        mock_download_episode.assert_called_once_with("http://test.com/rss")
                        mock_transcribe_audio.assert_called_once_with("podcasts/new_episode.mp3")
                        mock_summarize_text.assert_called_once_with("transcription.txt")
                        mock_send_email.assert_called_once_with(
                            "Podcast Summary: New Episode",
                            "This is a summary.",
                            "<p>Here is the summary for <b>New Episode</b>:</p><p>This is a summary.</p>",
                            "test@example.com"
                        )
                        mock_episode_exists.assert_called_once_with("http://test.com/new_episode.mp3")
                        mock_add_episode.assert_called_once()

    @patch('main_workflow.download_latest_podcast_episode')
    @patch('main_workflow.time.sleep')
    def test_main_workflow_episode_already_processed(self, mock_sleep, mock_download_episode):
        # Mock download_latest_podcast_episode to return an existing episode
        mock_download_episode.return_value = {
            "episode_title": "Existing Episode",
            "episode_url": "http://test.com/existing_episode.mp3",
            "file_path": "podcasts/existing_episode.mp3",
            "is_new_download": False,
            "published_date": "2025-07-27T09:00:00"
        }

        with patch('database_manager.get_all_podcast_configs') as mock_get_all_podcast_configs:
            with patch('database_manager.episode_exists') as mock_episode_exists:
                with patch('database_manager.add_episode') as mock_add_episode:
                    with patch('main_workflow.time.sleep') as mock_sleep_inner:

                        mock_get_all_podcast_configs.return_value = [
                            {"name": "Test Podcast", "rss_feed_url": "http://test.com/rss", "recipient_email": "test@example.com"}
                        ]
                        mock_episode_exists.return_value = True # Episode already exists in DB

                        # To stop the infinite loop after one iteration
                        mock_sleep_inner.side_effect = [KeyboardInterrupt]

                        try:
                            process_podcasts()
                        except KeyboardInterrupt:
                            pass

                        mock_download_episode.assert_called_once_with("http://test.com/rss")
                        mock_episode_exists.assert_called_once_with("http://test.com/existing_episode.mp3")
                        mock_add_episode.assert_not_called() # Should not add if episode already exists

    @patch('main_workflow.download_latest_podcast_episode')
    @patch('main_workflow.transcribe_audio')
    @patch('main_workflow.summarize_text')
    @patch('main_workflow.send_email')
    @patch('main_workflow.time.sleep')
    def test_main_workflow_multiple_podcasts(self, mock_sleep, mock_send_email, mock_summarize_text, mock_transcribe_audio, mock_download_episode):
        # Mock download_latest_podcast_episode for Podcast A
        mock_download_episode.side_effect = [
            {
                "episode_title": "New Episode A",
                "episode_url": "http://test.com/new_episodeA.mp3",
                "file_path": "podcasts/new_episodeA.mp3",
                "is_new_download": True,
                "published_date": "2025-07-27T10:00:00"
            },
            # Mock download_latest_podcast_episode for Podcast B
            {
                "episode_title": "New Episode B",
                "episode_url": "http://test.com/new_episodeB.mp3",
                "file_path": "podcasts/new_episodeB.mp3",
                "is_new_download": True,
                "published_date": "2025-07-27T11:00:00"
            }
        ]
        mock_transcribe_audio.side_effect = ["transcriptionA.txt", "transcriptionB.txt"]
        mock_summarize_text.side_effect = ["Summary A", "Summary B"]
        mock_send_email.side_effect = [True, True]

        with patch('database_manager.get_all_podcast_configs') as mock_get_all_podcast_configs:
            with patch('database_manager.episode_exists') as mock_episode_exists:
                with patch('database_manager.add_episode') as mock_add_episode:
                    with patch('main_workflow.time.sleep') as mock_sleep_inner:

                        mock_get_all_podcast_configs.return_value = [
                            {"name": "Podcast A", "rss_feed_url": "http://test.com/rssA", "recipient_email": "a@test.com"},
                            {"name": "Podcast B", "rss_feed_url": "http://test.com/rssB", "recipient_email": "b@test.com"}
                        ]
                        mock_episode_exists.side_effect = [False, False] # Both episodes do not exist in DB
                        mock_add_episode.side_effect = [True, True] # Both episodes added successfully

                        # To stop the infinite loop after one iteration
                        mock_sleep_inner.side_effect = [KeyboardInterrupt]

                        try:
                            process_podcasts()
                        except KeyboardInterrupt:
                            pass

                        # Assertions for Podcast A
                        mock_download_episode.assert_any_call("http://test.com/rssA")
                        mock_transcribe_audio.assert_any_call("podcasts/new_episodeA.mp3")
                        mock_summarize_text.assert_any_call("transcriptionA.txt")
                        mock_send_email.assert_any_call(
                            "Podcast Summary: New Episode A",
                            "Summary A",
                            "<p>Here is the summary for <b>New Episode A</b>:</p><p>Summary A</p>",
                            "a@test.com"
                        )
                        mock_episode_exists.assert_any_call("http://test.com/new_episodeA.mp3")
                        mock_add_episode.assert_any_call({
                            "podcast_url": "http://test.com/rssA",
                            "episode_url": "http://test.com/new_episodeA.mp3",
                            "title": "New Episode A",
                            "published_date": "2025-07-27T10:00:00",
                            "audio_filepath": "podcasts/new_episodeA.mp3",
                            "transcription_filepath": "transcriptionA.txt",
                            "summary_filepath": "transcriptionA.summary.txt",
                            "summary_text": "Summary A"
                        })

                        # Assertions for Podcast B
                        mock_download_episode.assert_any_call("http://test.com/rssB")
                        mock_transcribe_audio.assert_any_call("podcasts/new_episodeB.mp3")
                        mock_summarize_text.assert_any_call("transcriptionB.txt")
                        mock_send_email.assert_any_call(
                            "Podcast Summary: New Episode B",
                            "Summary B",
                            "<p>Here is the summary for <b>New Episode B</b>:</p><p>Summary B</p>",
                            "b@test.com"
                        )
                        mock_episode_exists.assert_any_call("http://test.com/new_episodeB.mp3")
                        mock_add_episode.assert_any_call({
                            "podcast_url": "http://test.com/rssB",
                            "episode_url": "http://test.com/new_episodeB.mp3",
                            "title": "New Episode B",
                            "published_date": "2025-07-27T11:00:00",
                            "audio_filepath": "podcasts/new_episodeB.mp3",
                            "transcription_filepath": "transcriptionB.txt",
                            "summary_filepath": "transcriptionB.summary.txt",
                            "summary_text": "Summary B"
                        })

                        self.assertEqual(mock_add_episode.call_count, 2)
