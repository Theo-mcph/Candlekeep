import json
import ollama
from pathlib import Path
import argparse
import os
from tqdm import tqdm
import sys

from langchain_text_splitters import RecursiveCharacterTextSplitter





PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json" 

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)





parser = argparse.ArgumentParser(description="Summarize a Candlekeep session transcript")
parser.add_argument("--config", action="store_true", help="Use the transcript path specified in config.json instead of auto-detecting the most recent one")

args = parser.parse_args()

if args.config:
    print("Using transcript path from config.json")
    transcript_path = PROJECT_ROOT / config["summarization"]["manual_transcript_path"]

else:
    print("Auto-detecting most recent transcript")
    campaign_dir = PROJECT_ROOT / config["output_dir"] / config["campaign_name"]
    transcript_list = list(Path(campaign_dir).rglob("*.txt"))
    transcript_path = max(transcript_list, key=lambda transcript: transcript.stat().st_mtime)


print(f"Using transcript: {transcript_path}")

with open(transcript_path, "r", encoding="utf-8") as f:
    transcript_text = f.read()


def chunk_transcript(text: str, max_chars: int = 4000) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
                                            chunk_size=max_chars,
                                            chunk_overlap=200,
                                            length_function=len,
                                            is_separator_regex=False,)
    chunks = splitter.split_text(text)                                
    
    return chunks
#just a test 

transcript_segments = chunk_transcript(transcript_text)

summary_segments = []
segment_prompt = config["summarization"]["initial_prompt"]

for transcript_segment in tqdm(transcript_segments, desc=f"Summarizing {len(transcript_segments)} chunks", ascii="~~~~~~"):

    response = ollama.chat(
    model=config["summarization"]["model"],
    messages=[{"role": "user", "content": f"{segment_prompt} {transcript_segment}"}],
)

    summary_text = response["message"]["content"]
    summary_segments.append(summary_text)
    print(summary_text)