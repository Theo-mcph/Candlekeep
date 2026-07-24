import os
import json
from faster_whisper import WhisperModel
from pathlib import Path
from tqdm import tqdm
import sys

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json" 

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)


def run_transcription_pipeline(config):

    
    campaign_name = config["campaign_name"]
    output_dir = PROJECT_ROOT / config["output_dir"] / config["campaign_name"]
    output_file_name =config["output_file_name"]
    initial_prompt = config["initial_prompt"]
    speaker_mapping =config["speaker_mapping"]
    model_size = config["model_size"]
    hotwords_list =" ".join(config["hotwords"])
    

    print(f"Loading local Whisper model ({model_size}) onto GPU...")

    model = WhisperModel(model_size, device=config["device"], compute_type="float16")
    all_segments = []
    failed_speakers = []

    audio_dir = PROJECT_ROOT / config["input_dir"]

    if not audio_dir.is_dir():
        os.makedirs(audio_dir, exist_ok = True)
        print("folder not found creating new folder. Please place files in audio_dir directory")


# TODO: this assumes Craig's "number-username.ext" filename format.
# If we ever switch back to a custom py-cord/discord.py recording bot,
# revisit this parsing logic to match whatever naming convention that uses.

    for file in audio_dir.iterdir():
        if file.suffix == ".flac" or file.suffix == ".wav":

            speaker_id = file.stem.split("-", 1)[1]
            character_name = speaker_mapping.get(speaker_id, speaker_id)
            
    
            print(f"Transcribing {file}")

#transcription begins here
            try:
                segments, info = model.transcribe(
                                                    audio=str(file),
                                                    language=config["language"],
                                                    initial_prompt=initial_prompt,
                                                    beam_size=config["beam_size"],
                                                    vad_filter=True,
                                                    hotwords=hotwords_list,
                                                )
    #progress bar
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

            except Exception as e:    
                print(f"{character_name}'s audio file is damaged. \n{e}")
                response = input("Continue transcription anyway? (y/n): ")
                response = response.lower()

                if response == "y" or response == "yes":
                    failed_speakers.append(character_name)
                    continue

                else:
                    sys.exit()

    if not all_segments:
            print("No audio files were found to transcribe.")
            return

    # TODO: currently assumes any file that decodes without raising an exception
# has real content. A file with valid headers but no actual audio (0 duration,
# 0 segments) won't trigger the try/except below, and will just silently
# produce no transcript for that speaker. Worth catching explicitly if/when
# the workflow becomes more automated (e.g. no manual file-size eyeballing).


    all_segments.sort(key=lambda item: item['start'])

    info_file = audio_dir / "info.txt"

    session_date = None

    with open(info_file, "r") as f:
        for line in f:
            if line.startswith("Start time:"):
                session_date = line.split()[2].split("T")[0]

    if session_date is None:
        session_date = "unknown-date"
    
    
    final_output_path = Path(output_dir) / f"{campaign_name}-{output_file_name}-{session_date}"
    os.makedirs(final_output_path, exist_ok = True)
    output_file = os.path.join(final_output_path,f"{campaign_name}-{output_file_name}-{session_date}.txt")


    with open(output_file, "w", encoding="utf-8") as f:

        if failed_speakers:
            f.write("the following speaker(s) audio recording could not be transcribed\n")
            for name in failed_speakers:
                f.write(f"{name}\n")
            f.write("\n")

        for seg in all_segments:

            minutes, seconds = divmod(int(seg["start"]), 60) 
            
            timestamp = f"[{minutes:02d}:{seconds:02d}]"

            output_line = f"{timestamp} {seg['speaker']}: {seg['text']}"

            f.write(output_line + "\n")

    print("\nTranscription complete")
    print(f"\nfind your transcript here {final_output_path}")

if __name__ == "__main__":
    run_transcription_pipeline(config)

