import feedparser
import requests
import os
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

def download_latest_podcast_episode(rss_feed_url, download_directory="podcasts"):
    """
    Downloads the latest episode from a given podcast RSS feed.

    Args:
        rss_feed_url (str): The URL of the podcast's RSS feed.
        download_directory (str): The directory where the podcast episode will be saved.
    """
    logger.info(f"Parsing RSS feed from: {rss_feed_url}")
    try:
        feed = feedparser.parse(rss_feed_url)
    except Exception as e:
        logger.error(f"Error parsing RSS feed {rss_feed_url}: {e}")
        return None

    if not feed.entries:
        logger.warning("No episodes found in the RSS feed.")
        return None

    # Get the latest episode (first entry in the feed)
    latest_episode = feed.entries[0]
    episode_title = latest_episode.title
    episode_url = None

    # Find the audio enclosure
    for link in latest_episode.links:
        if 'type' in link and link.type.startswith('audio/'):
            episode_url = link.href
            break

    if not episode_url:
        logger.warning(f"No audio enclosure found for episode: {episode_title}")
        return None

    logger.info(f"Found latest episode: {episode_title}")
    logger.info(f"Download URL: {episode_url}")

    # Create the download directory if it doesn't exist
    if not os.path.exists(download_directory):
        try:
            os.makedirs(download_directory)
            logger.info(f"Created directory: {download_directory}")
        except OSError as e:
            logger.error(f"Error creating directory {download_directory}: {e}")
            return None

    # Construct the filename
    # Sanitize the title to create a valid filename
    import re
    filename = re.sub(r'[<>:"/\\|?*!]', '', episode_title).strip()
    
    # Get file extension from the URL, removing any query parameters
    from urllib.parse import urlparse
    parsed_url = urlparse(episode_url)
    path_without_query = parsed_url.path
    file_extension = os.path.splitext(path_without_query)[1]
    
    if not file_extension:
        # Fallback if extension is not in URL, e.g., .mp3
        file_extension = ".mp3"
    
    file_path = os.path.join(download_directory, f"{filename}{file_extension}")

    is_new_download = False
    if os.path.exists(file_path):
        logger.info(f"File already exists: {file_path}. Skipping download.")
    else:
        logger.info(f"Downloading '{episode_title}' to '{file_path}'...")
        try:
            response = requests.get(episode_url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Successfully downloaded: {file_path}")
            is_new_download = True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading episode: {e}")
            return None # Indicate failure to download
        except IOError as e:
            logger.error(f"Error writing episode to file {file_path}: {e}")
            return None

    return {
        "episode_title": episode_title,
        "episode_url": episode_url,
        "file_path": file_path,
        "is_new_download": is_new_download
    }
