import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_NAME = "summacast.db"

def connect_db():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        logger.info(f"Successfully connected to database: {DATABASE_NAME}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def create_table():
    """Creates the episodes table if it doesn't exist."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    podcast_url TEXT NOT NULL,
                    episode_url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    published_date TEXT,
                    audio_filepath TEXT,
                    transcription_filepath TEXT,
                    summary_filepath TEXT,
                    summary_text TEXT,
                    processed_timestamp TEXT
                )
            """)
            conn.commit()
            logger.info("Table 'episodes' checked/created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating table: {e}")
        finally:
            conn.close()
    create_podcast_configs_table()

def create_podcast_configs_table():
    """Creates the podcast_configs table if it doesn't exist."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS podcast_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    rss_feed_url TEXT NOT NULL UNIQUE,
                    recipient_email TEXT
                )
            """)
            conn.commit()
            logger.info("Table 'podcast_configs' checked/created successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating podcast_configs table: {e}")
        finally:
            conn.close()

def add_episode(episode_data):
    """
    Adds a new episode record to the database.
    episode_data is a dictionary containing episode details.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO episodes (
                    podcast_url, episode_url, title, published_date,
                    audio_filepath, transcription_filepath, summary_filepath, summary_text, processed_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                episode_data.get('podcast_url'),
                episode_data.get('episode_url'),
                episode_data.get('title'),
                episode_data.get('published_date'),
                episode_data.get('audio_filepath'),
                episode_data.get('transcription_filepath'),
                episode_data.get('summary_filepath'),
                episode_data.get('summary_text'),
                datetime.now().isoformat()
            ))
            conn.commit()
            logger.info(f"Added episode '{episode_data.get('title')}' to database.")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Episode '{episode_data.get('title')}' (URL: {episode_data.get('episode_url')}) already exists in database. Skipping.")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding episode to database: {e}")
            return False
        finally:
            conn.close()

def get_episode_by_url(episode_url):
    """
    Retrieves an episode record by its episode URL.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM episodes WHERE episode_url = ?", (episode_url,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving episode by URL {episode_url}: {e}")
            return None
        finally:
            conn.close()

def episode_exists(episode_url):
    """
    Checks if an episode with the given URL already exists in the database.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM episodes WHERE episode_url = ?", (episode_url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking if episode exists for URL {episode_url}: {e}")
            return False
        finally:
            conn.close()

def episode_exists(episode_url):
    """
    Checks if an episode with the given URL already exists in the database.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM episodes WHERE episode_url = ?", (episode_url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking if episode exists for URL {episode_url}: {e}")
            return False
        finally:
            conn.close()

def get_all_episodes():
    """
    Retrieves all episode records from the database, ordered by published date descending.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM episodes ORDER BY published_date DESC")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all episodes: {e}")
            return []
        finally:
            conn.close()

def get_episode_by_id(episode_id):
    """
    Retrieves an episode record by its ID.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving episode by ID {episode_id}: {e}")
            return None
        finally:
            conn.close()

def episode_exists(episode_url):
    """
    Checks if an episode with the given URL already exists in the database.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM episodes WHERE episode_url = ?", (episode_url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking if episode exists for URL {episode_url}: {e}")
            return False
        finally:
            conn.close()

def get_all_episodes():
    """
    Retrieves all episode records from the database, ordered by published date descending.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM episodes ORDER BY published_date DESC")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all episodes: {e}")
            return []
        finally:
            conn.close()

def get_episode_by_id(episode_id):
    """
    Retrieves an episode record by its ID.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving episode by ID {episode_id}: {e}")
            return None
        finally:
            conn.close()

def add_podcast_config(name, rss_feed_url, recipient_email=None):
    """
    Adds a new podcast configuration to the database.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO podcast_configs (name, rss_feed_url, recipient_email) VALUES (?, ?, ?)
            """, (name, rss_feed_url, recipient_email))
            conn.commit()
            logger.info(f"Added podcast config: {name} - {rss_feed_url}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Podcast config '{name}' (URL: {rss_feed_url}) already exists in database. Skipping.")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding podcast config: {e}")
            return False
        finally:
            conn.close()

def get_all_podcast_configs():
    """
    Retrieves all podcast configurations from the database.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM podcast_configs")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all podcast configs: {e}")
            return []
        finally:
            conn.close()

def delete_podcast_config(podcast_id):
    """
    Deletes a podcast configuration from the database by its ID.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM podcast_configs WHERE id = ?", (podcast_id,))
            conn.commit()
            logger.info(f"Deleted podcast config with ID: {podcast_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting podcast config: {e}")
            return False
        finally:
            conn.close()

def get_podcast_config_by_id(podcast_id):
    """
    Retrieves a podcast configuration by its ID.
    """
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM podcast_configs WHERE id = ?", (podcast_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving podcast config by ID {podcast_id}: {e}")
            return None
        finally:
            conn.close()

if __name__ == "__main__":
    # Example Usage
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    create_table()

    # Add a dummy episode
    dummy_episode_data = {
        "podcast_url": "http://example.com/podcast_feed.xml",
        "episode_url": "http://example.com/episode1.mp3",
        "title": "My First Episode",
        "published_date": "2025-07-27T10:00:00",
        "audio_filepath": "podcasts/episode1.mp3",
        "transcription_filepath": "transcriptions/episode1.txt",
        "summary_filepath": "summaries/episode1.summary.txt",
        "summary_text": "This is a summary of my first episode."
    }
    add_episode(dummy_episode_data)

    # Try to add the same episode again (should be skipped)
    add_episode(dummy_episode_data)

    # Check if an episode exists
    if episode_exists("http://example.com/episode1.mp3"):
        logger.info("Episode 1 exists in DB.")
    else:
        logger.info("Episode 1 does NOT exist in DB.")

    # Retrieve an episode
    retrieved_episode = get_episode_by_url("http://example.com/episode1.mp3")
    if retrieved_episode:
        logger.info(f"Retrieved episode: {retrieved_episode['title']}")
    else:
        logger.info("Episode not found.")

    # Add another episode
    dummy_episode_data_2 = {
        "podcast_url": "http://example.com/podcast_feed.xml",
        "episode_url": "http://example.com/episode2.mp3",
        "title": "My Second Episode",
        "published_date": "2025-07-27T11:00:00",
        "audio_filepath": "podcasts/episode2.mp3",
        "transcription_filepath": "transcriptions/episode2.txt",
        "summary_filepath": "summaries/episode2.summary.txt",
        "summary_text": "This is a summary of my second episode."
    }
    add_episode(dummy_episode_data_2)

    # Clean up (optional, for testing)
    # conn = connect_db()
    # if conn:
    #     cursor = conn.cursor()
    #     cursor.execute("DROP TABLE IF EXISTS episodes")
    #     conn.commit()
    #     conn.close()
    #     logger.info("Cleaned up database.")
