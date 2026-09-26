import os
import sys
from pathlib import Path
from sarvamai import SarvamAI

# Load .env if present and not already exported in the shell environment
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("\"'")
                if key and not os.environ.get(key):
                    os.environ[key] = val

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    print("Error: SARVAM_API_KEY is not set. Please add your key to .env file.")
    sys.exit(1)

client = SarvamAI(api_subscription_key=api_key)

response = client.chat.completions(
    model="sarvam-105b-conversations",
    messages=[
        {"role": "user", "content": "Hello! Please introduce yourself in one short sentence."}
    ],
)

print(response.choices[0].message.content)
