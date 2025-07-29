import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import logging

# Add the parent directory to the sys.path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
import database_manager

class TestApp(unittest.TestCase):

    def setUp(self):
        # Disable logging during tests to prevent clutter
        logging.disable(logging.CRITICAL)
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Clean up any existing database file
        if os.path.exists(database_manager.DATABASE_NAME):
            os.remove(database_manager.DATABASE_NAME)
        database_manager.create_table()
        database_manager.create_podcast_configs_table()

    def tearDown(self):
        # Re-enable logging after tests
        logging.disable(logging.NOTSET)
        # Clean up any created files and database
        if os.path.exists(database_manager.DATABASE_NAME):
            os.remove(database_manager.DATABASE_NAME)

    @patch('database_manager.get_all_episodes')
    @patch('database_manager.get_all_podcast_configs')
    def test_index_page(self, mock_get_all_podcast_configs, mock_get_all_episodes):
        mock_get_all_episodes.return_value = []
        mock_get_all_podcast_configs.return_value = []
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No podcasts configured yet.', response.data)
        self.assertIn(b'No episodes processed yet.', response.data)

    @patch('database_manager.get_all_podcast_configs')
    @patch('database_manager.add_podcast_config')
    @patch('database_manager.get_all_episodes')
    def test_add_podcast_post(self, mock_get_all_episodes, mock_add_podcast_config, mock_get_all_podcast_configs):
        mock_add_podcast_config.return_value = True
        mock_get_all_episodes.return_value = []
        mock_get_all_podcast_configs.return_value = [{'name': 'Test Podcast', 'rss_feed_url': 'http://test.com/rss'}]
        response = self.client.post('/add_podcast', data={
            'podcast_name': 'Test Podcast',
            'rss_feed_url': 'http://test.com/rss'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<h3>Test Podcast</h3>', response.data)
        mock_add_podcast_config.assert_called_once_with('Test Podcast', 'http://test.com/rss')

    @patch('database_manager.get_episode_by_id')
    def test_view_summary_page(self, mock_get_episode_by_id):
        mock_episode = {
            'id': 1,
            'title': 'Test Episode',
            'podcast_url': 'http://test.com/podcast',
            'episode_url': 'http://test.com/episode1',
            'published_date': '2025-01-01',
            'audio_filepath': 'audio.mp3',
            'transcription_filepath': 'transcription.txt',
            'summary_filepath': 'summary.txt',
            'summary_text': 'This is a test summary.'
        }
        mock_get_episode_by_id.return_value = mock_episode
        response = self.client.get('/summaries/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Summary for Test Episode', response.data)
        self.assertIn(b'This is a test summary.', response.data)

    @patch('database_manager.get_episode_by_id')
    @patch('transcribe_podcast.transcribe_audio')
    @patch('summarize_podcast.summarize_text')
    @patch('database_manager.connect_db')
    def test_resummarize_episode_success(self, mock_connect_db, mock_summarize_text, mock_transcribe_audio, mock_get_episode_by_id):
        mock_episode = {
            'id': 1,
            'title': 'Old Episode',
            'podcast_url': 'http://test.com/podcast',
            'episode_url': 'http://test.com/old_episode.mp3',
            'published_date': '2025-01-01',
            'audio_filepath': 'podcasts/old_episode.mp3',
            'transcription_filepath': 'transcriptions/old_episode.txt',
            'summary_filepath': 'summaries/old_episode.summary.txt',
            'summary_text': 'This is an old summary.'
        }
        mock_transcribe_audio.return_value = 'transcriptions/old_episode.txt'
        new_summary_text = 'This is a new summary.'
        mock_summarize_text.return_value = new_summary_text

        # Mock database update
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect_db.return_value = mock_conn

        # Prepare the updated episode for the second call to get_episode_by_id (after redirect)
        updated_mock_episode = mock_episode.copy()
        updated_mock_episode['summary_text'] = new_summary_text
        mock_get_episode_by_id.side_effect = [mock_episode.copy(), updated_mock_episode, updated_mock_episode]

        response = self.client.post('/resummarize/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'This is a new summary.', response.data)
        
        # Assert that get_episode_by_id was called twice (once by resummarize, once by index after redirect)
        self.assertEqual(mock_get_episode_by_id.call_count, 2)
        self.assertEqual(mock_get_episode_by_id.call_args_list[0].args[0], 1)
        self.assertEqual(mock_get_episode_by_id.call_args_list[1].args[0], 1)

        mock_transcribe_audio.assert_called_once_with('podcasts/old_episode.mp3')
        mock_summarize_text.assert_called_once_with('transcriptions/old_episode.txt')
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch('database_manager.get_episode_by_id')
    def test_resummarize_episode_not_found(self, mock_get_episode_by_id):
        mock_get_episode_by_id.return_value = None
        response = self.client.post('/resummarize/999')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Episode not found', response.data)

if __name__ == '__main__':
    unittest.main()
