
import os
import sqlite3
import unittest
from unittest.mock import patch
import shutil

# Add the parent directory to the path to allow imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from populate_db_from_files import populate_db_from_files
import database_manager

class TestPopulateDbFromFiles(unittest.TestCase):

    def setUp(self):
        self.test_podcasts_dir = "test_podcasts_dir"
        self.test_db = "test_summacast.db"
        os.makedirs(self.test_podcasts_dir, exist_ok=True)
        # Create dummy podcast directories
        os.makedirs(os.path.join(self.test_podcasts_dir, "Podcast 1"), exist_ok=True)
        os.makedirs(os.path.join(self.test_podcasts_dir, "Podcast 2"), exist_ok=True)
        # Create a dummy file to ensure it's ignored
        with open(os.path.join(self.test_podcasts_dir, "not_a_podcast.txt"), "w") as f:
            f.write("hello")

        # Set up a clean test database before each test
        database_manager.DATABASE_NAME = self.test_db
        conn = database_manager.connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS podcast_configs")
            conn.commit()
            conn.close()
        database_manager.create_podcast_configs_table()


    def tearDown(self):
        shutil.rmtree(self.test_podcasts_dir)
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_populate_db_from_files(self):
        # Run the function to test
        populate_db_from_files(podcasts_dir=self.test_podcasts_dir, db_name=self.test_db)

        # Verify the results
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM podcast_configs ORDER BY name")
        podcasts = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertEqual(len(podcasts), 2)
        self.assertEqual(podcasts[0], "Podcast 1")
        self.assertEqual(podcasts[1], "Podcast 2")

if __name__ == '__main__':
    unittest.main()
