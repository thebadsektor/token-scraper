import os
import re
import pandas as pd

# Directory where uploaded token .txt files are located
base_dir = "jina_scrapes"
files = [f for f in os.listdir(base_dir) if f.endswith(".txt")]

# Helpers
def extract_field(pattern, text, group=1, default=None):
    match = re.search(pattern, text)
    return match.group(group).strip() if match else default

def normalize_currency(val):
    if not val:
        return None
    val = val.replace("$", "").replace(",", "").strip()
    return float(val.replace("K", "")) * 1_000 if "K" in val else float(val)

def extract_creator_address(content):
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "Created by" in line:
            for j in range(i, i + 5):
                if "0x" in lines[j]:
                    addr = re.search(r"(0x[a-fA-F0-9]{40})", lines[j])
                    if addr:
                        return addr.group(1)
    return None

def extract_token_name(content):
    # Priority 1: full name before underline (e.g., ---- or ====)
    match = re.search(r"\n([A-Z][A-Za-z0-9 .!?\-']{3,})\n[-=]{3,}", content)
    if match:
        return match.group(1).strip()
    # Priority 2: after token image or before "Meme"
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "Meme" in line and i > 0:
            candidate = lines[i-1].strip()
            if 3 < len(candidate) < 40:
                return candidate
    return None

def extract_token_symbol(content):
    # e.g. "GM / BNB"
    match = re.search(r"\n([A-Z0-9]+)\s*/\s*BNB", content)
    if match:
        return match.group(1)
    # Fallback: use line before CA if looks like a ticker
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "CA:" and i > 0:
            candidate = lines[i-1].strip()
            if candidate.isupper() and 2 <= len(candidate) <= 5:
                return candidate
    return None

# Main extraction
def extract_token_data(file_name, content):
    return {
        "token_address": file_name.replace(".txt", ""),
        "token_name": extract_token_name(content),
        "symbol": extract_token_symbol(content),
        "creation_time": extract_field(r"Creation Time\s+([0-9:/\s]+)", content),
        "market_cap_usd": normalize_currency(extract_field(r"Market Cap\s+\$(\d[\d.,K]*)", content)),
        "virtual_liquidity_usd": normalize_currency(extract_field(r"Virtual Liquidity\$(\d[\d.,K]*)", content)),
        "volume_usd": normalize_currency(extract_field(r"Volume\$(\d[\d.,K]*)", content)),
        "bonding_curve_target": normalize_currency(extract_field(r"market cap reaches \$(\d[\d.,K]*)", content)),
        "mev_protection": extract_field(r"MEV protection\s+(\d+%)", content),
        "total_supply": extract_field(r"Total Supply\s*:\s*([\d,]+)", content),
        "creator_address": extract_creator_address(content)
    }

# Run parser
token_records = []
for fname in files:
    with open(os.path.join(base_dir, fname), "r", encoding="utf-8") as f:
        content = f.read()
        token_records.append(extract_token_data(fname, content))

df_tokens = pd.DataFrame(token_records)

# Save
output_path = os.path.join(base_dir, "parsed_tokens_dataset.csv")
df_tokens.to_csv(output_path, index=False)
print(f"✅ Saved parsed dataset to: {output_path}")
