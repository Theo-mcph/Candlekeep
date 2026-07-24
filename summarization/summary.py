import json
import ollama
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description="Summarize a Candlekeep session transcript")
parser.add_argument("--config", action="store_true", help="Use the transcript path specified in config.json instead of auto-detecting the most recent one")

args = parser.parse_args()

if args.config:
    print("Using transcript path from config.json")
else:
    print("Auto-detecting most recent transcript")
    