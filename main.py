import json
import requests
import time
import os

# Load high-score token addresses
with open("scores.json", "r") as f:
    scores_data = json.load(f)

token_addresses = [
    entry["token"]
    for entry in scores_data
    if entry.get("score") == 100
]

# Jina API auth key
JINA_API_KEY = "jina_dcf22ee63c8f4033958fa78fbbe27ba7dbR89F-lB8RfoTM1eiXozmISX2zd"

# Output folder
os.makedirs("jina_scrapes", exist_ok=True)

# Enrichment function
def enrich_with_jina(token_address):
    target_url = f"https://four.meme/token/{token_address}"
    jina_url = f"https://r.jina.ai/{target_url}"

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "X-No-Cache": "true",
        "X-With-Images-Summary": "true",
        "X-With-Links-Summary": "true",
    }

    try:
        response = requests.get(jina_url, headers=headers)
        response.raise_for_status()
        content = response.text

        # Trim image/link section
        end_idx = content.rfind("Images:")
        if end_idx != -1:
            content = content[:end_idx].strip()

        return content

    except Exception as e:
        return f"Error: {e}"

# Loop through tokens
for token in token_addresses:
    print(f"Scraping {token}...")
    content = enrich_with_jina(token)
    with open(f"jina_scrapes/{token}.txt", "w", encoding="utf-8") as f:
        f.write(content)
    time.sleep(0.3)  # ~200 RPM safe buffer

print("✅ Done scraping. Files saved in /jina_scrapes")
