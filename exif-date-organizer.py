import os
import sys
import re
import logging
import argparse
import traceback
from collections import Counter
from datetime import datetime
from PIL import Image, ExifTags

# --- HEIC SUPPORT CHECK ---
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

# --- PROGRESS BAR SUPPORT ---
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

# =======================
# KONFIGURASI GLOBAL
# =======================
LOG_FILENAME = "renamer.log"
# Support kedua-dua case (huruf besar/kecil handled by .lower() logic)
IMAGE_EXT = ('.jpg', '.jpeg', '.png', '.tiff', '.heic')
VIDEO_EXT = ('.mp4', '.mov', '.avi', '.mkv', '.3gp', '.m4v')
DATE_OUTPUT_FORMAT = "%Y-%m-%d"  # ISO Standard (Universal)

# =======================
# SETUP LOGGING
# =======================
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# =======================
# UTILITI
# =======================

def setup_arguments():
    parser = argparse.ArgumentParser(description="Cross-Platform Media Folder Renamer (ISO Standard).")
    
    # Path argument handling
    parser.add_argument("path", help="Path to the target directory containing folders to rename")
    parser.add_argument("--live", action="store_true", help="Execute actual renaming (Default is Dry Run)")
    parser.add_argument("--confidence", type=float, default=0.6, help="Majority confidence threshold (0.0 - 1.0). Default: 0.6")
    parser.add_argument("--non-interactive", action="store_true", help="Run without asking for user input (Skip on missing metadata)")
    
    return parser.parse_args()

def clean_folder_name(foldername):
    """Buang tarikh lama/sampah dari nama folder."""
    # Regex ini selamat untuk semua OS
    cleaned = re.sub(r"^[\d\.\-\/\s]+", "", foldername)
    if not cleaned.strip():
        return foldername
    return cleaned.strip()

def get_unique_path(path):
    """Generate unique path if folder exists (OS safe)"""
    counter = 1
    base = path
    while os.path.exists(path):
        path = f"{base} ({counter})"
        counter += 1
    return path

def normalize_date(date_str):
    try:
        # Standard EXIF format is usually YYYY:MM:DD HH:MM:SS
        dt_obj = datetime.strptime(str(date_str).split(" ")[0], "%Y:%m:%d")
        return dt_obj
    except (ValueError, TypeError):
        return None

def get_filesystem_date(filepath):
    # Cross-platform way to get modification time
    try:
        ts = os.path.getmtime(filepath)
        return datetime.fromtimestamp(ts)
    except OSError:
        return None

# =======================
# METADATA EXTRACTION
# =======================

def get_date_from_image(filepath):
    try:
        with Image.open(filepath) as img:
            exif = img.getexif()
            if not exif: return None
            # 36867 = DateTimeOriginal, 306 = DateTime
            date_str = exif.get(36867) or exif.get(306)
            if date_str: return normalize_date(date_str)
    except Exception as e:
        logging.debug(f"Image Error ({os.path.basename(filepath)}): {e}")
    return None

def get_date_from_video(filepath):
    try:
        # Hachoir handle path dengan betul ikut OS
        parser = createParser(filepath)
        if not parser: return None
        with parser:
            metadata = extractMetadata(parser)
            if metadata and metadata.has("creation_date"):
                return metadata.get("creation_date")
    except Exception:
        logging.debug(f"Video Error ({os.path.basename(filepath)}): {traceback.format_exc()}")
    return None

def handle_missing_metadata(filename, foldername, non_interactive):
    if non_interactive:
        logging.info(f"[AUTO-SKIP] Metadata missing for {filename} (Non-interactive)")
        return "IGNORE", None

    print(f"\n\n[!] Metadata TIADA: {filename}")
    print(f"    Folder: {foldername}")
    
    while True:
        c = input("    [S]kip Folder | [I]gnore File | [M]anual Date | [Q]uit >> ").upper()
        
        if c == "S": 
            logging.info(f"[USER] Skipped folder '{foldername}'")
            return "SKIP_FOLDER", None
        elif c == "I": 
            logging.info(f"[USER] Ignored file '{filename}'")
            return "IGNORE", None
        elif c == "Q": 
            sys.exit(0)
        elif c == "M":
            m = input("    Enter Date (YYYY-MM-DD): ").strip()
            try:
                d = datetime.strptime(m, "%Y-%m-%d")
                logging.info(f"[USER] Manual date {m} for {filename}")
                return "MANUAL", d
            except ValueError:
                print("    Invalid format.")

# =======================
# CORE LOGIC
# =======================

def process_folders(args):
    # Normalkan path input supaya selamat untuk OS semasa
    target_path = os.path.abspath(args.path)
    
    dry_run = not args.live
    min_confidence = args.confidence
    
    print(f"\n{'='*40}")
    print(f" PLATFORM: {sys.platform}")
    print(f" MODE    : {'[DRY RUN]' if dry_run else '[LIVE]'}")
    print(f" PATH    : {target_path}")
    if not HEIC_SUPPORTED:
        print(" [!] NOTE: 'pillow-heif' not installed. HEIC skipped.")
    print(f"{'='*40}\n")

    if not os.path.exists(target_path):
        print(f"Error: Path '{target_path}' tidak wujud!")
        return

    # os.walk is cross-platform friendly
    for dirpath, dirnames, filenames in os.walk(target_path, topdown=False):
        folder = os.path.basename(dirpath)
        
        # Filter files (case-insensitive check for Unix/Windows compatibility)
        media_files = [f for f in filenames if f.lower().endswith(IMAGE_EXT + VIDEO_EXT)]
        
        if not media_files: continue

        date_counter = Counter()
        skip_folder = False

        print(f"Processing: {folder} ({len(media_files)} files)")

        iterator = tqdm(media_files, unit="file") if TQDM_AVAILABLE else media_files

        for file in iterator:
            path = os.path.join(dirpath, file) # Auto-handle / or \
            date_obj = None

            if file.lower().endswith(IMAGE_EXT): date_obj = get_date_from_image(path)
            elif file.lower().endswith(VIDEO_EXT): date_obj = get_date_from_video(path)

            if not date_obj:
                if TQDM_AVAILABLE: iterator.clear()
                action, value = handle_missing_metadata(file, folder, args.non_interactive)
                if TQDM_AVAILABLE: iterator.refresh()

                if action == "SKIP_FOLDER": 
                    skip_folder = True
                    break
                if action == "MANUAL": date_obj = value
                if action == "IGNORE": continue 
            
            if not date_obj: date_obj = get_filesystem_date(path)

            if date_obj:
                date_str = date_obj.strftime("%Y-%m-%d")
                date_counter[date_str] += 1

        if skip_folder or not date_counter: continue

        # Decision Making
        most_common_date_str, count = date_counter.most_common(1)[0]
        confidence = count / sum(date_counter.values())

        if confidence < min_confidence:
            print(f"   -> [SKIP] Low Confidence ({confidence:.2f})")
            logging.warning(f"Skipped {folder}: Low confidence")
            continue

        # Renaming Logic
        clean_name = clean_folder_name(folder)
        date_final = datetime.strptime(most_common_date_str, "%Y-%m-%d")
        new_name = f"{date_final.strftime(DATE_OUTPUT_FORMAT)} {clean_name}"

        if new_name == folder:
            continue

        parent = os.path.dirname(dirpath)
        new_path = get_unique_path(os.path.join(parent, new_name))

        if dry_run:
            print(f"   -> [DRY] '{folder}' --> '{new_name}'")
        else:
            try:
                os.rename(dirpath, new_path)
                print(f"   -> [OK] Renamed to: {new_name}")
                logging.info(f"RENAMED: '{dirpath}' -> '{new_path}'")
            except OSError as e:
                logging.error(f"Failed to rename {dirpath}: {e}")
                print(f"   -> [ERROR] Failed to rename. Check log.")

# =======================
# MAIN
# =======================
if __name__ == "__main__":
    if not HEIC_SUPPORTED:
        logging.warning("Module 'pillow-heif' missing. HEIC files skipped.")
    
    args = setup_arguments()
    
    try:
        process_folders(args)
    except KeyboardInterrupt:
        print("\n\nOperasi dibatalkan.")
        sys.exit()
    except Exception:
        logging.critical("Fatal Error:", exc_info=True)
        print("\n[CRITICAL ERROR] See log file.")
