#!/usr/bin/env python3
import os
import json
import glob
import requests
from collections import defaultdict

# Base GitHub API path for the repo
GITHUB_API = "https://api.github.com/repos/SukkaLab/ruleset.skk.moe/contents/sing-box"

def download_folder(subfolder):
    """Download all JSON files from a GitHub repo subfolder."""
    url = f"{GITHUB_API}/{subfolder}"
    os.makedirs(subfolder, exist_ok=True)
    print(f"\n📥 Downloading JSON files from {url}")

    resp = requests.get(url)
    resp.raise_for_status()
    files = resp.json()

    for file in files:
        if file["name"].endswith(".json"):
            raw_url = file["download_url"]
            dest = os.path.join(subfolder, file["name"])
            print(f"  ↳ {file['name']}")
            content = requests.get(raw_url).content
            with open(dest, "wb") as f:
                f.write(content)


def extract_rules(data):
    """Extract formatted rule lines from JSON structure."""
    lines = []
    for rule in data.get("rules", []):
        for d in rule.get("domain", []):
            lines.append(f"full:{d}")
        for d in rule.get("domain_suffix", []):
            lines.append(f"domain:{d}")
        for d in rule.get("domain_keyword", []):
            lines.append(f"keyword:{d}")
        for d in rule.get("domain_regex", []):
            lines.append(f"regexp:{d}")
    return lines


def load_json_rules(folder):
    """Load all JSON files in a folder → dict[basename] = [rules]."""
    rules_map = defaultdict(list)
    for path in glob.glob(os.path.join(folder, "*.json")):
        base = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            rules_map[base].extend(extract_rules(data))
        except Exception as e:
            print(f"⚠️ Failed to process {path}: {e}")
    return rules_map


def main():
    folders = ["domainset", "non_ip"]
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Download the JSON files
    for folder in folders:
        download_folder(folder)

    # Step 2: Combine rules by filename
    combined = defaultdict(list)
    for folder in folders:
        folder_rules = load_json_rules(folder)
        for name, rules in folder_rules.items():
            combined[name].extend(rules)

    # Step 3: Write to data/ directory
    for name, rules in combined.items():
        output_file = os.path.join(output_dir, name)
        seen = set()
        unique_rules = [r for r in rules if not (r in seen or seen.add(r))]
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(unique_rules))
        print(f"✅ Wrote {output_file} ({len(unique_rules)} rules)")

    print("\n🎉 All done! Results saved in ./data/")


if __name__ == "__main__":
    main()
