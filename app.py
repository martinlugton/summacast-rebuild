from flask import Flask, render_template, request, redirect, url_for
import database_manager
import os
import json
import logging

app = Flask(__name__)

# Configure logging for Flask app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PODCAST_CONFIG_FILE = "podcast_config.json"

def load_podcast_config():
    if os.path.exists(PODCAST_CONFIG_FILE):
        try:
            with open(PODCAST_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error(f"Could not decode {PODCAST_CONFIG_FILE}. Please check its format.")
            return []
    else:
        logging.warning(f"Podcast configuration file not found: {PODCAST_CONFIG_FILE}. Starting with empty config.")
        return []

@app.route('/')
def index():
    database_manager.create_table() # Ensure table exists
    episodes = database_manager.get_all_episodes() # Assuming this function exists or will be created
    podcast_configs = load_podcast_config()
    return render_template('index.html', episodes=episodes, podcast_configs=podcast_configs)

@app.route('/add_podcast', methods=['GET', 'POST'])
def add_podcast():
    if request.method == 'POST':
        podcast_name = request.form['podcast_name']
        rss_feed_url = request.form['rss_feed_url']
        
        podcast_configs = load_podcast_config()
        if not podcast_configs:
            podcast_configs = []
        
        podcast_configs.append({"name": podcast_name, "rss_feed_url": rss_feed_url})
        
        try:
            with open(PODCAST_CONFIG_FILE, 'w') as f:
                json.dump(podcast_configs, f, indent=4)
            logging.info(f"Added new podcast to config: {podcast_name} - {rss_feed_url}")
            return redirect(url_for('index'))
        except IOError as e:
            logging.error(f"Error saving podcast config: {e}")
            return "Error saving podcast configuration", 500
            
    return render_template('add_podcast.html')

@app.route('/summaries/<int:episode_id>')
def view_summary(episode_id):
    episode = database_manager.get_episode_by_id(episode_id) # Assuming this function exists or will be created
    if episode:
        return render_template('summary.html', episode=episode)
    return "Episode not found", 404

@app.route('/resummarize/<int:episode_id>', methods=['POST'])
def resummarize_episode(episode_id):
    episode = database_manager.get_episode_by_id(episode_id)
    if not episode:
        logging.error(f"Attempted to re-summarize non-existent episode with ID: {episode_id}")
        return "Episode not found", 404

    logging.info(f"Re-summarizing episode: {episode['title']}")

    # Assuming audio_filepath and transcription_filepath are stored in the DB
    audio_file_path = episode['audio_filepath']
    transcription_file_path = episode['transcription_filepath']

    # Re-transcribe if transcription file doesn't exist or is needed
    if not os.path.exists(transcription_file_path):
        logging.info(f"Transcription file not found for {episode['title']}, re-transcribing...")
        from transcribe_podcast import transcribe_audio
        transcription_file_path = transcribe_audio(audio_file_path)
        if not transcription_file_path:
            logging.error(f"Failed to re-transcribe audio for episode: {episode['title']}")
            return "Failed to re-transcribe audio", 500

    # Re-summarize
    from summarize_podcast import summarize_text
    new_summary_text = summarize_text(transcription_file_path)

    if new_summary_text:
        # Update the summary in the database
        conn = database_manager.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE episodes SET summary_text = ?, processed_timestamp = ? WHERE id = ?",
                               (new_summary_text, datetime.now().isoformat(), episode_id))
                conn.commit()
                logging.info(f"Successfully re-summarized and updated episode {episode['title']}")
            except sqlite3.Error as e:
                logging.error(f"Error updating summary in DB for episode {episode['title']}: {e}")
                return "Error updating summary", 500
            finally:
                conn.close()
        return redirect(url_for('view_summary', episode_id=episode_id))
    else:
        logging.error(f"Failed to generate new summary for episode: {episode['title']}")
        return "Failed to generate summary", 500

if __name__ == '__main__':
    app.run(debug=True)
