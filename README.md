# Summacast

Summacast is a Python-based application designed to automate the process of downloading, transcribing, summarizing, and emailing podcast episodes. It runs continuously in the background, checking for new episodes from configured RSS feeds.

## How to Run the Summacast Software Locally

The Summacast software is designed to run continuously in the background, checking for new podcast episodes, processing them, and sending email summaries.

**Prerequisites:**

1.  **Python 3.x:** Ensure you have Python installed on your Windows machine.
2.  **Git:** (Already installed, as you're in a Git repository).
3.  **Gemini CLI:** You need to have the Gemini CLI installed and configured with your Google Cloud credentials. The `summarize_podcast.py` script relies on this.
4.  **Whisper:** The `transcribe_podcast.py` script uses the Whisper model. It will download the "medium" model the first time it runs.

**Setup Steps:**

1.  **Navigate to the project directory:**
    ```bash
    cd C:\git\summacast-rebuild
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` doesn't exist, you'll need to manually install `feedparser`, `requests`, `python-dotenv`, `APScheduler`, `Flask`, and `whisper` using `pip install <package_name>`.)*
3.  **Configure Environment Variables (`.env` file):**
    Create a file named `.env` in the root of your project (`C:\git\summacast-rebuild\.env`) and add your AhaSend API key and email addresses:
    ```
    AHASEND_API_KEY=your_ahasend_api_key
    SENDER_EMAIL=your_verified_sender_email@example.com
    RECIPIENT_EMAIL=your_recipient_email@example.com
    ```
    *Replace the placeholder values with your actual credentials.*
4.  **Configure Podcast Sources (`podcast_config.json` file):**
    Create a file named `podcast_config.json` in the root of your project (`C:\git\summacast-rebuild\podcast_config.json`) and add the RSS feed URLs of the podcasts you want to process:
    ```json
    [
        {
            "name": "NPR Up First",
            "rss_feed_url": "https://www.npr.org/rss/podcast.php?id=510019",
            "summary_length": "medium"
        },
        {
            "name": "Example Podcast 2",
            "rss_feed_url": "http://example.com/podcast2.xml",
            "summary_length": "short"
        }
    ]
    ```
    *You can add as many podcast entries as you like, and specify `summary_length` as "short", "medium", or "long".*

**Running the Software:**

To start the continuous podcast processing workflow, open your command prompt or terminal in the project root and run:

```bash
python main_workflow.py
```

**What will happen:**

*   The script will start running in the background, managed by APScheduler.
*   It will periodically (default: every hour) check each podcast listed in `podcast_config.json` for new episodes.
*   **Logging Output:** You will see informational messages printed to your console, indicating:
    *   When it's checking for new episodes.
    *   When a new episode is found.
    *   When an episode is being downloaded, transcribed, summarized, and emailed.
    *   Any errors or warnings encountered during the process.
*   **File Creation:**
    *   Downloaded audio files will be saved in the `podcasts/` directory.
    *   Transcription files (`.txt`) and summary files (`.summary.txt`) will be created alongside the audio files.
    *   A SQLite database file named `summacast.db` will be created in the project root to keep track of processed episodes.
*   **Email Notifications:** When a new episode is fully processed, an email containing its summary will be sent to the `RECIPIENT_EMAIL` specified in your `.env` file.

To stop the software, you can usually press `Ctrl+C` in the terminal where it's running.

To run the web interface, open a separate command prompt or terminal in the project root and run:

```bash
python app.py
```

**What will happen:**

*   The Flask development server will start, usually on `http://127.0.0.1:5000/`.
*   You can access the web interface by opening your web browser and navigating to that address.
*   The web interface allows you to:
    *   View a list of configured podcasts.
    *   View a list of processed episodes and their summaries.
    *   Add new podcast RSS feeds with specified summary lengths.

---

### Architectural Explanation

The Summacast software is designed with a modular architecture, separating concerns into distinct Python modules.

**Core Components:**

*   **`main_workflow.py` (Orchestrator & Scheduler):**
    *   This is the central control unit for the podcast processing.
    *   It uses `APScheduler` to periodically run the `process_podcasts` function.
    *   It loads podcast configurations from `podcast_config.json`.
    *   It iterates through each configured podcast and coordinates the entire process by calling functions from other modules: `download_podcast`, `transcribe_podcast`, `summarize_podcast`, and `send_email`.
    *   It uses `database_manager` to check if an episode has already been processed and to record new processed episodes.
    *   Handles overall logging for the workflow.

*   **`download_podcast.py` (Downloader):**
    *   Responsible for parsing RSS feeds (using `feedparser`).
    *   Identifies the latest podcast episode and its audio enclosure URL.
    *   Downloads the audio file (using `requests`) to the `podcasts/` directory.
    *   Includes logic to skip downloading if the file already exists locally.
    *   Returns episode metadata, including the `published_date`, to the `main_workflow`.

*   **`transcribe_podcast.py` (Transcriber):**
    *   Takes an audio file path as input.
    *   Uses the local Whisper model to transcribe the audio into text.
    *   Saves the transcription to a `.txt` file.
    *   Returns the path to the transcription file.

*   **`summarize_podcast.py` (Summarizer):**
    *   Takes a transcription text file path and a `length` parameter (short, medium, or long) as input.
    *   Constructs a prompt based on the desired summary length.
    *   Interacts with the Gemini CLI (via `subprocess`) to generate a summary of the text.
    *   Saves the generated summary to a `.summary.txt` file.
    *   Returns the summary text.

*   **`send_email.py` (Email Sender):**
    *   Takes subject, plain text body, and HTML body as input.
    *   Uses the AhaSend REST API (via `requests`) to send an email.
    *   Retrieves API credentials from the `.env` file.

*   **`database_manager.py` (Persistent Storage):**
    *   Manages interactions with a local SQLite database (`summacast.db`).
    *   Provides functions to:
        *   Connect to the database.
        *   Create the `episodes` table (if it doesn't exist).
        *   Add new episode records (including podcast URL, episode URL, title, published date, file paths, and summary text).
        *   Check if an episode (by its URL) already exists in the database.
        *   Retrieve all episodes or a specific episode by ID for the web interface.

*   **`app.py` (Web Interface):**
    *   A Flask application that provides a simple web-based user interface.
    *   Defines routes for:
        *   `/`: Displays a list of configured podcasts and processed episodes.
        *   `/add_podcast`: Provides a form to add new podcast RSS feeds and their desired summary lengths.
        *   `/summaries/<episode_id>`: Displays the detailed summary of a specific episode.
    *   Interacts with `database_manager.py` to fetch and display data.
    *   Manages saving new podcast configurations to `podcast_config.json`.

*   **`podcast_config.json` (Configuration):**
    *   A JSON file that stores a list of podcast entries, each containing a `name`, `rss_feed_url`, and `summary_length`. This allows easy management of multiple podcast sources without modifying code.

*   **`.env` (Credentials):**
    *   A plain text file (ignored by Git) that securely stores sensitive information like API keys and email addresses, keeping them out of the codebase.

*   **`templates/` (Web Templates):**
    *   Contains HTML files (`index.html`, `add_podcast.html`, `summary.html`) that define the structure and content of the web interface.

This architecture ensures modularity, maintainability, and extensibility, allowing for future enhancements.
