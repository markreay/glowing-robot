#! /usr/bin/env python3 

import os
import json
import shutil
from PIL import Image
import re
import hashlib
from tqdm import tqdm

# Paths
json_dir = os.path.expanduser("~/src/zoe/zoe-nexus-data/storage/zoe-nexus/zoe/images")
output_dir = os.path.expanduser("~/src/zoe/glowing-robot-images/photos")

# Size mapping
size_map = {
    "thumbnail": 100,
    "small": 200,
    "medium": 400,
    "large": 800,
    "full": None,  # Full size, no resizing
}

# Ensure output dir exists
os.makedirs(output_dir, exist_ok=True)

def slugify(title):
    """Convert a title string to a URL-friendly slug."""
    title = title.lower()
    title = re.sub(r'[^a-z0-9]+', '-', title)
    title = re.sub(r'-+', '-', title).strip('-')
    return title

def md5sum(filepath):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Collect all JSON files
json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]

for file in tqdm(json_files, desc="Processing images", unit="file"):
    json_path = os.path.join(json_dir, file)
    with open(json_path, 'r') as f:
        data = json.load(f)

    md5_hash = data["md5_hash"]
    title_slug = slugify(data["title"])
    png_filename = md5_hash + ".png"
    png_path = os.path.join(json_dir, png_filename)
    md5_hash_short = md5_hash[:8]

    if not os.path.exists(png_path):
        tqdm.write(f"PNG not found for {json_path} - tried {png_filename}. Skipping.")
        continue

    # Build full-size output path
    full_out_path = os.path.join(output_dir, f"{title_slug}-{md5_hash_short}-full.png")

    # If -full exists and matches source hash, skip regenerating smaller versions
    if os.path.exists(full_out_path) and md5sum(full_out_path) == md5sum(png_path):
        #tqdm.write(f"Skipping {png_filename} — full image unchanged.")
        continue

    # Copy source 
    shutil.copy(png_path, full_out_path)

    # Open source image
    img = Image.open(png_path)

    # Save resized versions
    for size_name, size_value in size_map.items():
        if size_name == "full":
            continue
        resized_img = img.copy()
        resized_img.thumbnail((size_value, size_value))
        out_name = f"{title_slug}-{md5_hash_short}-{size_name}.png"
        resized_img.save(os.path.join(output_dir, out_name))

    # Save default medium size without suffix
    default_img = img.copy()
    default_img.thumbnail((size_map["medium"], size_map["medium"]))
    default_name = f"{title_slug}-{md5_hash_short}.png"
    default_img.save(os.path.join(output_dir, default_name))

    tqdm.write(f"Processed {png_filename} → outputs regenerated.")
