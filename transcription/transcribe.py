import os
import json
from faster_whisper import WhisperModel
from pathlib import Path
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json" 

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)


def run_transcription_pipeline(config):

    
    
    output_dir = config["output_dir"]
    output_file_name =config["output_file_name"]
    initial_prompt = config["initial_prompt"]
    speaker_mapping =config["speaker_mapping"]
    model_size = config["model_size"]
    hotwords_list =" ".join(config["hotwords"])

    print(f"Loading local Whisper model ({model_size}) onto GPU...")

    model = WhisperModel(model_size, device=config["device"], compute_type="float16")
    all_segments = []

    audio_dir =Path(config["input_dir"])

    if not audio_dir.is_dir():
        os.makedirs(audio_dir, exist_ok = True)
        print("folder not found creating new folder. Please place files in audio_dir directory")


    for file in audio_dir.iterdir():
        if file.suffix == ".flac" or file.suffix == ".wav":

            speaker_id = file.stem.split("-", 1)[1]
            character_name = speaker_mapping.get(speaker_id, speaker_id)
            
    
            print(f"Transcribing {file} on your 3060 Ti...")

            segments, info = model.transcribe(
                                                audio=str(file),
                                                language=config["language"],
                                                initial_prompt=initial_prompt,
                                                beam_size=config["beam_size"],
                                                vad_filter=True,
                                                hotwords=hotwords_list,
                                            )

            pbar = tqdm(total=info.duration, unit="sec", desc=f"Transcribing {file.name}", ascii = " ⋆˙⟡⊹₊")

            

            for segment in segments:
                all_segments.append({"start": segment.start,
                                    "speaker": character_name,
                                    "text":segment.text.strip()
                                    })
                elapsed_time = (segment.end - segment.start)
                pbar.update(elapsed_time)

            pbar.update(pbar.total - pbar.n) 
            pbar.close()

    if not all_segments:
            print("No audio files were found to transcribe.")
            return


    all_segments.sort(key=lambda item: item['start'])

    info_file = audio_dir / "info.txt"

    with open(info_file, "r") as f:
        for line in f:
            if line.startswith("Start time:"):
                session_date = line.split()[2].split("T")[0]

    
    
    final_output_path = Path(output_dir)/f"{output_file_name} - {session_date}"
    os.makedirs(final_output_path, exist_ok = True)
    output_file = os.path.join(final_output_path,f"{output_file_name} - {session_date}.txt")


    with open(output_file, "w", encoding="utf-8") as f:
        for seg in all_segments:

            minutes, seconds = divmod(int(seg["start"]), 60) 
            
            timestamp = f"[{minutes:02d}:{seconds:02d}]"

            output_line = f"{timestamp} {seg['speaker']}: {seg['text']}"

            f.write(output_line + "\n")

    print("\nTranscription complete")
    print(f"\nfind your transcript here {final_output_path}")

if __name__ == "__main__":
    run_transcription_pipeline(config)

