import os
from faster_whisper import WhisperModel

def run_transcription_pipeline():

    model_size = "base"

    print(f"Loading local Whisper model ({model_size}) onto GPU...")

    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    all_segments = []

audio_dir = "./workspace/projects/Candlekeep/recordings/test_session"

if not os.path.exists(audio_dir):
    os.makedirs(audio_dir, exist_ok = True)
    print("folder not found creating new folder. Please place files in audio_dir directory")

for file in os.listdir(audio_dir):
    if ".flac" in file or ".wav" in file:
       speaker_id = os.path.splitext(file)[0]
       













if __name__ == "__main__":
    run_transcription_pipeline()

