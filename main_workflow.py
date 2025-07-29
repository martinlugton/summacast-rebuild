import os
import json
import time
import logging
from download_podcast import download_latest_podcast_episode
from transcribe_podcast import transcribe_audio
from summarize_podcast import summarize_text
from send_email import send_email
import database_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

def process_podcasts():
    database_manager.create_table() # Ensure database table exists
    podcast_configs = database_manager.get_all_podcast_configs()
    if not podcast_configs:
        logging.error("No podcast configurations loaded. Skipping podcast processing.")
        return

    for config in podcast_configs:
        podcast_name = config.get("name", "Unknown Podcast")
        rss_feed_url = config.get("rss_feed_url")

        if not rss_feed_url:
            logging.warning(f"Skipping podcast {podcast_name}: No RSS feed URL provided.")
            continue

        logging.info(f"\nChecking for new episodes for '{podcast_name}' from {rss_feed_url}...")
        episode_info = download_latest_podcast_episode(rss_feed_url)

        if episode_info:
            episode_id = episode_info["episode_url"]
            if not database_manager.episode_exists(episode_id):
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
                                episode_data = {
                                    "podcast_url": rss_feed_url,
                                    "episode_url": episode_id,
                                    "title": episode_info["episode_title"],
                                    "published_date": episode_info["published_date"],
                                    "audio_filepath": audio_file_path,
                                    "transcription_filepath": transcription_file_path,
                                    "summary_filepath": os.path.splitext(transcription_file_path)[0] + ".summary.txt",
                                    "summary_text": summary
                                }
                                database_manager.add_episode(episode_data)
                                logging.info(f"Episode '{episode_info['episode_title']}' processed and added to database.")
                            else:
                                logging.error(f"Failed to send email for episode: {episode_info['episode_title']}")
                        else:
                            logging.warning(f"Could not summarize episode: {episode_info['episode_title']}")
                    else:
                        logging.warning(f"Could not transcribe episode: {episode_info['episode_title']}")
                else:
                    logging.info(f"Latest episode for '{podcast_name}' ({episode_info['episode_title']}) already exists locally.")
            else:
                logging.info(f"Episode '{episode_info['episode_title']}' for '{podcast_name}' already processed (found in DB).")
        else:
            logging.warning(f"No episode information returned for '{podcast_name}' or an error occurred during download.")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_podcasts, IntervalTrigger(minutes=15)) # Run every 15 minutes
    scheduler.start()
    logging.info("Scheduler started. Press Ctrl+C to exit.")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    try:
        # This is needed to keep the main thread alive for the scheduler to run
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        pass


