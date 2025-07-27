import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
import logging

# Add the parent directory to the sys.path to allow importing main_workflow
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main_workflow import main, PROCESSED_EPISODES_FILE, PODCAST_CONFIG_FILE

class TestMainWorkflow(unittest.TestCase):

    def setUp(self):
        # Disable logging during tests to prevent clutter
        logging.disable(logging.CRITICAL)
        # Clean up any existing processed_episodes.json or podcast_config.json
        if os.path.exists(PROCESSED_EPISODES_FILE):
            os.remove(PROCESSED_EPISODES_FILE)
        if os.path.exists(PODCAST_CONFIG_FILE):
            os.remove(PODCAST_CONFIG_FILE)

    def tearDown(self):
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)
        # Clean up any created files
        if os.path.exists(PROCESSED_EPISODES_FILE):
            os.remove(PROCESSED_EPISODES_FILE)
        if os.path.exists(PODCAST_CONFIG_FILE):
            os.remove(PODCAST_CONFIG_FILE)

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
            "is_new_download": True
        }
        mock_transcribe_audio.return_value = "transcription.txt"
        mock_summarize_text.return_value = "This is a summary."
        mock_send_email.return_value = True # Email sent successfully

        # Run main for one iteration
        with patch('main_workflow.load_podcast_config') as mock_load_config:
            with patch('main_workflow.load_processed_episodes') as mock_load_processed:
                with patch('main_workflow.save_processed_episodes') as mock_save_processed:

                    mock_load_config.return_value = [
                        {"name": "Test Podcast", "rss_feed_url": "http://test.com/rss"}
                    ]
                    mock_load_processed.return_value = {}

                    # To stop the infinite loop after one iteration
                    mock_sleep.side_effect = [KeyboardInterrupt]

                    try:
                        main()
                    except KeyboardInterrupt:
                        pass

                    mock_download_episode.assert_called_once_with("http://test.com/rss")
                    mock_transcribe_audio.assert_called_once_with("podcasts/new_episode.mp3")
                    mock_summarize_text.assert_called_once_with("transcription.txt")
                    mock_send_email.assert_called_once_with(
                        "Podcast Summary: New Episode",
                        "This is a summary.",
                        "<p>Here is the summary for <b>New Episode</b>:</p><p>This is a summary.</p>"
                    )
                    mock_save_processed.assert_called_once_with({"http://test.com/rss": ["http://test.com/new_episode.mp3"]})

    @patch('main_workflow.download_latest_podcast_episode')
    @patch('main_workflow.time.sleep')
    @patch('main_workflow.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_workflow_episode_already_processed(self, mock_open_builtin, mock_exists, mock_sleep, mock_download_episode):
        # Mock podcast_config.json content
        mock_exists.side_effect = [True, True, True] # podcast_config.json, processed_episodes.json, then for each episode
        mock_open_builtin.side_effect = [
            mock_open(read_data=json.dumps([
                {"name": "Test Podcast", "rss_feed_url": "http://test.com/rss"}
            ])).return_value, # For podcast_config.json
            mock_open(read_data=json.dumps({"http://test.com/rss": ["http://test.com/existing_episode.mp3"]})).return_value, # For processed_episodes.json (initial load)
        ]

        # Mock download_latest_podcast_episode to return an existing episode
        mock_download_episode.return_value = {
            "episode_title": "Existing Episode",
            "episode_url": "http://test.com/existing_episode.mp3",
            "file_path": "podcasts/existing_episode.mp3",
            "is_new_download": False # Important: it's not a new download
        }

        with patch('main_workflow.load_podcast_config') as mock_load_config:
            with patch('main_workflow.load_processed_episodes') as mock_load_processed:
                with patch('main_workflow.save_processed_episodes') as mock_save_processed:

                    mock_load_config.return_value = [
                        {"name": "Test Podcast", "rss_feed_url": "http://test.com/rss"}
                    ]
                    mock_load_processed.return_value = {"http://test.com/rss": ["http://test.com/existing_episode.mp3"]}

                    # To stop the infinite loop after one iteration
                    mock_sleep.side_effect = [KeyboardInterrupt]

                    try:
                        main()
                    except KeyboardInterrupt:
                        pass

                    mock_download_episode.assert_called_once_with("http://test.com/rss")
                    mock_save_processed.assert_not_called() # Should not save if episode already processed

    @patch('main_workflow.download_latest_podcast_episode')
    @patch('main_workflow.transcribe_audio')
    @patch('main_workflow.summarize_text')
    @patch('main_workflow.send_email')
    @patch('main_workflow.time.sleep')
    @patch('main_workflow.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_workflow_multiple_podcasts(self, mock_open_builtin, mock_exists, mock_sleep, mock_send_email, mock_summarize_text, mock_transcribe_audio, mock_download_episode):
        # Mock podcast_config.json content for two podcasts
        mock_exists.side_effect = [True, True, True, True] # podcast_config.json, processed_episodes.json, then for each episode
        mock_open_builtin.side_effect = [
            mock_open(read_data=json.dumps([
                {"name": "Podcast A", "rss_feed_url": "http://test.com/rssA"},
                {"name": "Podcast B", "rss_feed_url": "http://test.com/rssB"}
            ])).return_value, # For podcast_config.json
            mock_open(read_data=json.dumps({})).return_value, # For processed_episodes.json (initial load)
            mock_open().return_value, # For processed_episodes.json (save after Podcast A)
            mock_open().return_value # For processed_episodes.json (save after Podcast B)
        ]

        # Mock download_latest_podcast_episode for Podcast A
        mock_download_episode.side_effect = [
            {
                "episode_title": "New Episode A",
                "episode_url": "http://test.com/new_episodeA.mp3",
                "file_path": "podcasts/new_episodeA.mp3",
                "is_new_download": True
            },
            # Mock download_latest_podcast_episode for Podcast B
            {
                "episode_title": "New Episode B",
                "episode_url": "http://test.com/new_episodeB.mp3",
                "file_path": "podcasts/new_episodeB.mp3",
                "is_new_download": True
            }
        ]
        mock_transcribe_audio.side_effect = ["transcriptionA.txt", "transcriptionB.txt"]
        mock_summarize_text.side_effect = ["Summary A", "Summary B"]
        mock_send_email.side_effect = [True, True]

        with patch('main_workflow.load_podcast_config') as mock_load_config:
            with patch('main_workflow.load_processed_episodes') as mock_load_processed:
                with patch('main_workflow.save_processed_episodes') as mock_save_processed:

                    mock_load_config.return_value = [
                        {"name": "Podcast A", "rss_feed_url": "http://test.com/rssA"},
                        {"name": "Podcast B", "rss_feed_url": "http://test.com/rssB"}
                    ]
                    mock_load_processed.return_value = {}

                    # To stop the infinite loop after one iteration
                    mock_sleep.side_effect = [KeyboardInterrupt]

                    try:
                        main()
                    except KeyboardInterrupt:
                        pass

                    # Assertions for Podcast A
                    mock_download_episode.assert_any_call("http://test.com/rssA")
                    mock_transcribe_audio.assert_any_call("podcasts/new_episodeA.mp3")
                    mock_summarize_text.assert_any_call("transcriptionA.txt")
                    mock_send_email.assert_any_call(
                        "Podcast Summary: New Episode A",
                        "Summary A",
                        "<p>Here is the summary for <b>New Episode A</b>:</p><p>Summary A</p>"
                    )

                    # Assertions for Podcast B
                    mock_download_episode.assert_any_call("http://test.com/rssB")
                    mock_transcribe_audio.assert_any_call("podcasts/new_episodeB.mp3")
                    mock_summarize_text.assert_any_call("transcriptionB.txt")
                    mock_send_email.assert_any_call(
                        "Podcast Summary: New Episode B",
                        "Summary B",
                        "<p>Here is the summary for <b>New Episode B</b>:</p><p>Summary B</p>"
                    )

                    # Verify save_processed_episodes was called twice
                    self.assertEqual(mock_save_processed.call_count, 2)
                    # Verify the final state of the processed_episodes_tracker
                    final_tracker_state = mock_save_processed.call_args_list[1].args[0]
                    self.assertIn("http://test.com/new_episodeA.mp3", final_tracker_state["http://test.com/rssA"])
                    self.assertIn("http://test.com/new_episodeB.mp3", final_tracker_state["http://test.com/rssB"])

if __name__ == '__main__':
    unittest.main()
