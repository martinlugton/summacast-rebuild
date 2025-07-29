import os
import subprocess
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

def summarize_text(text_filepath):
    """
    Summarizes the content of a given text file using the Gemini CLI.

    Args:
        text_filepath (str): The path to the text file to summarize.

    Returns:
        str: The summarized text.
    """
    try:
        with open(text_filepath, 'r', encoding='utf-8') as f:
            text_content = f.read()

        # Construct the full prompt to send to Gemini
        full_prompt = f"""Produce a summary of the key points in this podcast transcript. The summary should be a highly detailed list. It should be between 300 and 750 words. For each point, give at least one concrete example immediately after it. Ignore episode credits and advertising in this summary. Once you have done this, please then highlight a key quote from the episode, under the heading '<h3>Key Quote</h3>'. Once you have done that, please list some limitations of the arguments made in the transcript, and potential divergent viewpoints, under the heading '<h3>Potential Limitations and Divergent Views</h3>'. Limit this section to a maximum of 250 words, and a maximum of 4 points.\n\n{text_content}\n\nSummary:"""

        # Construct the Gemini CLI command to read from stdin
        command = ["cmd.exe", "/c", "gemini", "--model", "gemini-1.5-pro"]

        # Execute the command, piping the full prompt to stdin
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate(input=full_prompt)

        if process.returncode != 0:
            error_message = f"Gemini CLI command failed with exit code {process.returncode}.\nStdout: {stdout}\nStderr: {stderr}"
            logger.error(error_message)
            return None

        summary = stdout.strip()

        summary_filepath = os.path.splitext(text_filepath)[0] + ".summary.txt"
        with open(summary_filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        logger.info(f"Summary saved to {summary_filepath}")
        return summary

    except FileNotFoundError:
        logger.error(f"Text file not found: {text_filepath}")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Gemini CLI command failed: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred during summarization: {e}")
        return None

if __name__ == "__main__":
    # Example usage (replace with actual path to a transcription file)
    # For testing, you might want to create a dummy transcription file
    dummy_transcription_file = "podcasts/dummy_transcription.txt"
    if not os.path.exists(dummy_transcription_file):
        with open(dummy_transcription_file, "w", encoding="utf-8") as f:
            f.write("This is a dummy transcription. It talks about various topics. This is a very long transcription that needs to be summarized. It has many sentences and paragraphs. The main points are that summarization is important and that this is a test.")
    
    summarize_text(dummy_transcription_file)
