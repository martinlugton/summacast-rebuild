import os
import database_manager

def populate_db_from_files(podcasts_dir='podcasts', db_name='summacast.db'):
    """Scans the specified directory and adds any subdirectories as podcasts to the database."""
    database_manager.DATABASE_NAME = db_name
    if not os.path.exists(podcasts_dir):
        print(f"Directory not found: {podcasts_dir}")
        return

    for podcast_name in os.listdir(podcasts_dir):
        podcast_path = os.path.join(podcasts_dir, podcast_name)
        if os.path.isdir(podcast_path):
            # We don't have the RSS feed URL, so we'll use the podcast name as a placeholder
            database_manager.add_podcast_config(podcast_name, podcast_name, "")

if __name__ == '__main__':
    populate_db_from_files()