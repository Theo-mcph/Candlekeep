import os
import json
from faster_whisper import WhisperModel
from pathlib import Path

def run_transcription_pipeline():

    model_size = "base"

    print(f"Loading local Whisper model ({model_size}) onto GPU...")

    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    all_segments = []

    audio_dir =Path("./recordings/test_session/")

    if not audio_dir.is_dir():
        os.makedirs(audio_dir, exist_ok = True)
        print("folder not found creating new folder. Please place files in audio_dir directory")


    for file in audio_dir.iterdir():
        if file.suffix == ".flac" or file.suffix == ".wav":

            speaker_id = file.stem.split("-", 1)[1]
            
    
            print(f"Transcribing {file} on your 3060 Ti...")

            segments ,info = model.transcribe(audio = str(file),language="en",)

            for segment in segments:
                all_segments.append({"start": segment.start,
                                    "speaker": speaker_id,
                                    "text":segment.text.strip()
                                    })


    if not all_segments:
            print("No audio files were found to transcribe.")
            return


    all_segments.sort(key=lambda item: item['start'])

    output_file = os.path.join(audio_dir,"transcript.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        for seg in all_segments:

            minutes, seconds = divmod(int(seg["start"]), 60) 
            
            timestamp = f"[{minutes:02d}:{seconds:02d}]"

            line = f"{timestamp} {seg['speaker']}: {seg['text']}"

            f.write(line + "\n")




if __name__ == "__main__":
    run_transcription_pipeline()

