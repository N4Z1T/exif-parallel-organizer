import os
import sys
import re
import logging
import argparse
import traceback
from collections import Counter
from datetime import datetime
from PIL import Image, ExifTags

# --- HEIC SUPPORT ---
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

# --- PROGRESS BAR ---
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

# =======================
# CONFIG
# =======================
LOG_FILENAME = "renamer_v7.log"
IMAGE_EXT = ('.jpg', '.jpeg', '.png', '.tiff', '.heic')
VIDEO_EXT = ('.mp4', '.mov', '.avi', '.mkv', '.3gp', '.m4v')
DATE_OUTPUT_FORMAT = "%Y-%m-%d"

# SENARAI FOLDER/FAIL SAMPAH YANG PERLU DISKIP (Synology & OS Junk)
IGNORED_DIRS = {'@eaDir', '#recycle', '.DS_Store', 'Thumbs.db'}
IGNORED_FILES = {'SYNOFILE_THUMB', 'desktop.ini', '.DS_Store'}

# =======================
# LOGGING
# =======================
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# =======================
# UTILS
# =======================
def setup_arguments():
    parser = argparse.ArgumentParser(description="Rename ONLY main folders based on recursive media dates (Synology Optimized).")
    parser.add_argument("path", help="Path induk (cth: /volume1/photo/2026)")
    parser.add_argument("--live", action="store_true", help="Jalankan rename sebenar")
    parser.add_argument("--confidence", type=float, default=0.6, help="Min confidence (0.0 - 1.0)")
    parser.add_argument("--non-interactive", action="store_true", help="Auto-skip jika tiada metadata")
    
    parser.add_argument("--case", 
                        choices=['title', 'upper', 'lower', 'sentence', 'original'], 
                        default='title',
                        help="Pilih format huruf: title (Default), upper, lower, sentence, original")
    
    return parser.parse_args()

def clean_folder_name(foldername, case_type='title'):
    cleaned = re.sub(r"^[\d\.\-\/\s]+", "", foldername)
    if not cleaned.strip(): return foldername
    cleaned = cleaned.strip()

    if case_type == 'upper': return cleaned.upper()
    elif case_type == 'lower': return cleaned.lower()
    elif case_type == 'title': return cleaned.title()
    elif case_type == 'sentence': return cleaned.capitalize()
    elif case_type == 'original': return cleaned
    
    return cleaned.title()

def get_unique_path(path):
    counter = 1
    base = path
    while os.path.exists(path):
        path = f"{base} ({counter})"
        counter += 1
    return path

def normalize_date(date_str):
    try:
        dt_obj = datetime.strptime(str(date_str).split(" ")[0], "%Y:%m:%d")
        return dt_obj
    except (ValueError, TypeError):
        return None

def get_filesystem_date(filepath):
    try:
        ts = os.path.getmtime(filepath)
        return datetime.fromtimestamp(ts)
    except OSError:
        return None

# =======================
# METADATA LOGIC
# =======================
def get_date_from_image(filepath):
    try:
        with Image.open(filepath) as img:
            exif = img.getexif()
            if not exif: return None
            date_str = exif.get(36867) or exif.get(306)
            if date_str: return normalize_date(date_str)
    except Exception:
        pass
    return None

def get_date_from_video(filepath):
    try:
        parser = createParser(filepath)
        if not parser: return None
        with parser:
            metadata = extractMetadata(parser)
            if metadata and metadata.has("creation_date"):
                return metadata.get("creation_date")
    except Exception:
        pass
    return None

def collect_dates_recursive(root_folder, non_interactive):
    date_counter = Counter()
    files_needing_input = [] 
    
    all_files = []
    
    # === UPDATED: Logic ignore @eaDir ===
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # 1. Skip folder sistem Synology (@eaDir) dari dilawati
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        
        for f in filenames:
            # 2. Skip fail sistem jika terserempak
            if any(junk in f for junk in IGNORED_FILES):
                continue

            if f.lower().endswith(IMAGE_EXT + VIDEO_EXT):
                all_files.append(os.path.join(dirpath, f))

    if not all_files:
        return None, False

    iterator = tqdm(all_files, unit="file", leave=False) if TQDM_AVAILABLE else all_files

    for filepath in iterator:
        date_obj = None
        if filepath.lower().endswith(IMAGE_EXT): date_obj = get_date_from_image(filepath)
        elif filepath.lower().endswith(VIDEO_EXT): date_obj = get_date_from_video(filepath)
        
        if date_obj:
            date_counter[date_obj.strftime("%Y-%m-%d")] += 1
        else:
            files_needing_input.append(filepath)

    for filepath in files_needing_input:
        if non_interactive:
            fs_date = get_filesystem_date(filepath)
            if fs_date: date_counter[fs_date.strftime("%Y-%m-%d")] += 1
            continue

        fname = os.path.basename(filepath)
        parent = os.path.basename(os.path.dirname(filepath))
        
        if TQDM_AVAILABLE: iterator.clear()
        
        print(f"\n[!] Metadata Missing: {fname} (in /{parent})")
        
        while True:
            c = input("    [S]kip Folder | [I]gnore File | [M]anual Date | [Q]uit >> ").upper()
            if c == 'Q': sys.exit(0)
            if c == 'S': return None, True 
            if c == 'I': break 
            if c == 'M':
                m = input("    YYYY-MM-DD: ").strip()
                try:
                    d = datetime.strptime(m, "%Y-%m-%d")
                    date_counter[d.strftime("%Y-%m-%d")] += 1
                    break
                except ValueError: print("    Invalid.")
        
        if TQDM_AVAILABLE: iterator.refresh()
    
    return date_counter, False

# =======================
# MAIN PROCESS
# =======================
def process_folders(args):
    target_path = os.path.abspath(args.path)
    dry_run = not args.live
    
    print(f"\n{'='*40}")
    print(f" TARGET: {target_path}")
    print(f" MODE  : {'[DRY RUN]' if dry_run else '[LIVE]'}")
    print(f" CASE  : {args.case.upper()}")
    print(f"{'='*40}\n")

    if not os.path.exists(target_path):
        print("Path not found.")
        return

    try:
        subdirs = [f.path for f in os.scandir(target_path) if f.is_dir()]
    except OSError as e:
        print(f"Error accessing path: {e}")
        return

    subdirs.sort()

    for folder_path in subdirs:
        folder_name = os.path.basename(folder_path)
        
        # Skip @eaDir di level utama juga
        if folder_name in IGNORED_DIRS: continue

        print(f"Processing: {folder_name}...")

        date_stats, should_skip = collect_dates_recursive(folder_path, args.non_interactive)

        if should_skip or not date_stats:
            logging.info(f"Skipped {folder_name}")
            continue

        most_common_date_str, count = date_stats.most_common(1)[0]
        total_files = sum(date_stats.values())
        confidence = count / total_files

        if confidence < args.confidence:
            print(f"   -> [SKIP] Low Confidence ({confidence:.2f})")
            continue

        clean_name = clean_folder_name(folder_name, args.case)
        
        date_final = datetime.strptime(most_common_date_str, "%Y-%m-%d")
        new_name = f"{date_final.strftime(DATE_OUTPUT_FORMAT)} {clean_name}"

        if new_name == folder_name:
            continue

        new_full_path = get_unique_path(os.path.join(target_path, new_name))

        if dry_run:
            print(f"   -> [DRY] {folder_name} \n            --> {new_name}")
        else:
            try:
                os.rename(folder_path, new_full_path)
                print(f"   -> [OK] Renamed to: {new_name}")
                logging.info(f"RENAMED: {folder_name} -> {new_name}")
            except OSError as e:
                print(f"   -> [ERROR] {e}")

if __name__ == "__main__":
    args = setup_arguments()
    try:
        process_folders(args)
    except KeyboardInterrupt:
        print("\nStopped.")
