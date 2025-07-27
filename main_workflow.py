import os
import json
import time
import logging
from download_podcast import download_latest_podcast_episode
from transcribe_podcast import transcribe_audio
from summarize_podcast import summarize_text
from send_email import send_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PODCAST_CONFIG_FILE = "podcast_config.json"
PROCESSED_EPISODES_FILE = "processed_episodes.json"

def load_podcast_config():
    if os.path.exists(PODCAST_CONFIG_FILE):
        try:
            with open(PODCAST_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Could not decode {PODCAST_CONFIG_FILE}. Please check its format.")
            return None
    else:
        logging.error(f"Podcast configuration file not found: {PODCAST_CONFIG_FILE}")
        return None

def load_processed_episodes():
    if os.path.exists(PROCESSED_EPISODES_FILE):
        try:
            with open(PROCESSED_EPISODES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Could not decode {PROCESSED_EPISODES_FILE}. Starting with empty tracker.")
            return {}
    return {}

def save_processed_episodes(episodes_tracker):
    try:
        with open(PROCESSED_EPISODES_FILE, 'w') as f:
            json.dump(episodes_tracker, f, indent=4)
    except IOError as e:
        logging.error(f"Error saving processed episodes to {PROCESSED_EPISODES_FILE}: {e}")

def main():
    check_interval_seconds = 3600  # Check every hour

    while True:
        podcast_configs = load_podcast_config()
        if not podcast_configs:
            logging.error("No podcast configurations loaded. Waiting for next check.")
            time.sleep(check_interval_seconds)
            continue

        processed_episodes_tracker = load_processed_episodes()

        for config in podcast_configs:
            podcast_name = config.get("name", "Unknown Podcast")
            rss_feed_url = config.get("rss_feed_url")

            if not rss_feed_url:
                logging.warning(f"Skipping podcast {podcast_name}: No RSS feed URL provided.")
                continue

            # Initialize tracker for this podcast if it doesn't exist
            if rss_feed_url not in processed_episodes_tracker:
                processed_episodes_tracker[rss_feed_url] = []

            logging.info(f"\nChecking for new episodes for '{podcast_name}' from {rss_feed_url}...")
            episode_info = download_latest_podcast_episode(rss_feed_url)

            if episode_info:
                episode_id = episode_info["episode_url"]
                if episode_id not in processed_episodes_tracker[rss_feed_url]:
                    if episode_info["is_new_download"]:
                        logging.info(f"New episode detected for '{podcast_name}': {episode_info['episode_title']}")

                        audio_file_path = episode_info["file_path"]
                        transcription_file_path = transcribe_audio(audio_file_path)

                        if transcription_file_path:
                            summary = summarize_text(transcription_file_path)
                            if summary:
                                subject = f"Podcast Summary: {episode_info['episode_title']}"
                                text_body = summary
                                html_body = f"<p>Here is the summary for <b>{episode_info['episode_title']}</b>:</p><p>{summary}</p>"
                                if send_email(subject, text_body, html_body):
                                    processed_episodes_tracker[rss_feed_url].append(episode_id)
                                    save_processed_episodes(processed_episodes_tracker)
                                    logging.info(f"Episode '{episode_info['episode_title']}' processed and added to tracker.")
                                else:
                                    logging.error(f"Failed to send email for episode: {episode_info['episode_title']}")
                            else:
                                logging.warning(f"Could not summarize episode: {episode_info['episode_title']}")
                        else:
                            logging.warning(f"Could not transcribe episode: {episode_info['episode_title']}")
                    else:
                        logging.info(f"Latest episode for '{podcast_name}' ({episode_info['episode_title']}) already exists locally.")
                else:
                    logging.info(f"Episode '{episode_info['episode_title']}' for '{podcast_name}' already processed.")
            else:
                logging.warning(f"No episode information returned for '{podcast_name}' or an error occurred during download.")

        logging.info(f"Waiting for {check_interval_seconds} seconds before next check...")
        time.sleep(check_interval_seconds)

if __name__ == "__main__":
    main()

