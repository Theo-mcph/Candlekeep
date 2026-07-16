import os
from faster_whisper import WhisperModel

def run_transcription_pipeline():

    model_size = "base"

    print(f"Loading local Whisper model ({model_size}) onto GPU...")

    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    all_segments = []

    audio_dir = "./workspace/projects/Candlekeep/recordings/test_session/"

    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir, exist_ok = True)
        print("folder not found creating new folder. Please place files in audio_dir directory")

    for file in os.listdir(audio_dir):
        if ".flac" in file or ".wav" in file:
            speaker_id = os.path.splitext(file)[0]
       
            file_path = os.path.join(audio_dir, file)
            print(f"Transcribing {file_path} on your 3060 Ti...")

            segments ,info = model.transcribe(audio = file_path,language="en",)

            for segment in segments:
                all_segments.append({"start": segment.start,
                                     "speaker": speaker_id,
                                     "text":segment.text.strip()
                                     })
    

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

