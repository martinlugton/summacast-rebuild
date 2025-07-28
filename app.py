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
        summary_length = request.form['summary_length']
        
        podcast_configs = load_podcast_config()
        if not podcast_configs:
            podcast_configs = []
        
        podcast_configs.append({"name": podcast_name, "rss_feed_url": rss_feed_url, "summary_length": summary_length})
        
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

if __name__ == '__main__':
    app.run(debug=True)
