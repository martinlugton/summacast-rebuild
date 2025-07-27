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

PROCESSED_EPISODES_FILE = "processed_episodes.json"

def load_processed_episodes():
    if os.path.exists(PROCESSED_EPISODES_FILE):
        try:
            with open(PROCESSED_EPISODES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Could not decode {PROCESSED_EPISODES_FILE}. Starting with empty list.")
            return []
    return []

def save_processed_episodes(episodes):
    try:
        with open(PROCESSED_EPISODES_FILE, 'w') as f:
            json.dump(episodes, f, indent=4)
    except IOError as e:
        logging.error(f"Error saving processed episodes to {PROCESSED_EPISODES_FILE}: {e}")

def main():
    rss_feed_url = "https://www.npr.org/rss/podcast.php?id=510019"  # Example RSS feed
    check_interval_seconds = 3600  # Check every hour

    processed_episodes = load_processed_episodes()

    while True:
        logging.info(f"\nChecking for new episodes from {rss_feed_url}...")
        episode_info = download_latest_podcast_episode(rss_feed_url)

        if episode_info and episode_info["is_new_download"]:
            episode_id = episode_info["episode_url"]
            if episode_id not in processed_episodes:
                logging.info(f"New episode detected: {episode_info["episode_title"]}")

                audio_file_path = episode_info["file_path"]
                transcription_file_path = transcribe_audio(audio_file_path)

                if transcription_file_path:
                    summary = summarize_text(transcription_file_path)
                    if summary:
                        subject = f"Podcast Summary: {episode_info["episode_title"]}"
                        text_body = summary
                        html_body = f"<p>Here is the summary for <b>{episode_info["episode_title"]}</b>:</p><p>{summary}</p>"
                        send_email(subject, text_body, html_body)
                        processed_episodes.append(episode_id)
                        save_processed_episodes(processed_episodes)
                        logging.info(f"Episode '{episode_info["episode_title"]}' processed and added to tracker.")
                    else:
                        logging.warning(f"Could not summarize episode: {episode_info["episode_title"]}")
                else:
                    logging.warning(f"Could not transcribe episode: {episode_info["episode_title"]}")
            else:
                logging.info(f"Episode {episode_info["episode_title"]} already processed.")
        elif episode_info and not episode_info["is_new_download"]:
            logging.info(f"Latest episode {episode_info["episode_title"]} already exists and is not new.")
        else:
            logging.warning("No episode information returned or an error occurred during download.")

        logging.info(f"Waiting for {check_interval_seconds} seconds before next check...")
        time.sleep(check_interval_seconds)

if __name__ == "__main__":
    main()
