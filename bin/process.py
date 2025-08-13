#! /usr/bin/env python3 

import os
import json
import shutil
from PIL import Image
import re
import hashlib
from tqdm import tqdm

# argument --force or -f to force regeneration of all images
import argparse

parser = argparse.ArgumentParser(description="Process and resize images based on JSON metadata.")
parser.add_argument('--force', '-f', action='store_true', help="Force regeneration of all images.")
args = parser.parse_args()  

force_regenerate = args.force
    
# Paths
json_dir = os.path.expanduser("~/src/zoe/zoe-nexus-data/storage/zoe-nexus/zoe/images")
output_dir = os.path.expanduser("~/src/zoe/glowing-robot-images/photos")
temp_dir = os.path.expanduser("~/src/zoe/glowing-robot-images/photos.tmp")

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
    if not force_regenerate and os.path.exists(full_out_path) and md5sum(full_out_path) == md5sum(png_path):
        #tqdm.write(f"Skipping {png_filename} — full image unchanged.")
        continue

    # Copy source 
    shutil.copy(png_path, full_out_path)

    def safe_save(img, out_path):
        """Save image with error handling."""
        """Also ensure that the output file is never partially written even if the process is interrpted."""

        out_path_dir, out_path_filename = os.path.split(out_path)
        temp_path = os.path.join(temp_dir, out_path_filename)
        os.makedirs(temp_dir, exist_ok=True)
        try:
            img.save(temp_path)
            os.replace(temp_path, out_path)  # Atomically replace the file
            tqdm.write(f"Saved {out_path}")
        except Exception as e:
            tqdm.write(f"Error saving {out_path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # Open source image
    img = Image.open(png_path)

    # Save resized versions
    for size_name, size_value in size_map.items():
        if size_name == "full":
            continue
        resized_img = img.copy()
        resized_img.thumbnail((size_value, size_value))
        out_name = f"{title_slug}-{md5_hash_short}-{size_name}.png"
        safe_save(resized_img, os.path.join(output_dir, out_name))
        if size_name == "medium":
            # Save default medium size without suffix
            default_name = f"{title_slug}-{md5_hash_short}.png"
            safe_save(resized_img, os.path.join(output_dir, default_name))

    tqdm.write(f"Processed {png_filename} → outputs regenerated.")
