import whisper
import os

def transcribe_audio(audio_file_path):
    print(f"Transcribing {audio_file_path}...")
    try:
        model = whisper.load_model("medium", device="cuda")
        print("Whisper model loaded. Starting transcription...")
        result = model.transcribe(audio_file_path)
        print("Transcription complete.")
        transcription_file_path = os.path.splitext(audio_file_path)[0] + ".txt"
        with open(transcription_file_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"Transcription saved to {transcription_file_path}")
        return transcription_file_path
    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return None

if __name__ == "__main__":
    # Example usage (replace with a valid audio file path)
    # Ensure you have an audio file in your 'podcasts' directory for testing
    # For example, if you downloaded an episode named 'My Podcast Episode.mp3'
    # audio_file = "podcasts/My Podcast Episode.mp3"
    # transcribed_file = transcribe_audio(audio_file)
    # if transcribed_file:
    #     print(f"Transcription available at: {transcribed_file}")
    print("This script is intended to be imported and used by other modules.")
    print("To test, uncomment the example usage and provide a valid audio file path.")
