# EXIF Date Organizer

A Python script to automatically organize and rename media folders based on the creation dates embedded in images and videos. This tool provides intelligent date extraction, confidence-based renaming, and optional AI-powered title casing and Malay spelling correction for a streamlined media management workflow.

## Features

*   **Automated Folder Renaming:** Renames media folders to a `YYYY-MM-DD Folder Name` format.
*   **Intelligent Date Extraction:** Accurately extracts creation dates from a wide range of image formats (JPG, JPEG, PNG, TIFF, HEIC) using EXIF data and from video formats (MP4, MOV, AVI, MKV, 3GP, M4V) using `hachoir`.
*   **Confidence-Based Renaming:** Implements a customizable confidence threshold (based on the most prevalent date within a folder) to prevent mis-renaming due to insufficient or ambiguous metadata.
*   **AI Integration (Optional):** Utilizes Google Generative AI (Gemma/Gemini) for advanced folder name processing:
    *   Converts folder names to proper Title Case.
    *   Corrects common Malay spelling errors.
    *   Preserves and respects acronyms (e.g., KADA, JKR, KPKM) in uppercase.
    *   Automatically selects the most suitable available Gemma or Gemini model.
*   **Dry Run Mode:** Offers a safe preview mode to simulate all renaming operations without making actual changes to your file system.
*   **Detailed Logging:** Comprehensive logs of all actions, including successful renames, skipped folders, and errors, are recorded in `exif-date-organizer.log`.
*   **System File Exclusion:** Automatically ignores common system-generated directories and files (e.g., `@eaDir`, `.DS_Store`, `Thumbs.db`).
*   **Duplicate Name Resolution:** Gracefully handles potential naming conflicts by appending numerical suffixes (e.g., `(1)`, `(2)`) to ensure unique folder paths.

## Installation

To use the EXIF Date Organizer, ensure you have Python 3 installed.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/N4Z1T/exif-date-organizer.git
    cd exif-date-organizer
    ```

2.  **Install core dependencies:**
    ```bash
    pip install Pillow requests tqdm
    ```

3.  **Install optional dependencies (highly recommended for full functionality):**
    *   **Video Metadata (Hachoir):** Essential for robust video date extraction.
        ```bash
        pip install hachoir
        ```
    *   **HEIC Support (Pillow-Heif):** Enables date extraction from HEIC image files.
        ```bash
        pip install pillow-heif
        ```

## Usage

Execute the script from your terminal, providing the target folder path and any desired options.

```bash
python exif-date-organizer.py <path_to_target_folder> [OPTIONS]
```

### Arguments

*   `<path_to_target_folder>` (Required): The absolute or relative path to the root directory containing the media folders you wish to organize.

### Options

*   `--live`: **Executes the renaming operations.** If this flag is omitted, the script will perform a dry run, reporting planned changes without modifying your files.
*   `--confidence <value>`: Sets the minimum confidence level (a float between 0.0 and 1.0) required for a folder to be renamed. This confidence is calculated based on the proportion of files sharing the most common creation date within that folder. Default is `0.6` (60%).
*   `--non-interactive`: (Currently reserved for future enhancements) Automatically handles cases of missing or insufficient metadata without requiring user input.
*   `--case <type>`: Defines the casing format for folder names when AI processing is not enabled. Valid options include `title`, `upper`, `lower`, and `sentence`. The default setting is `title`.
*   `--ai-api-key <YOUR_GOOGLE_AI_API_KEY>`: Your API Key from Google AI Studio. Providing this key enables the advanced AI-powered title casing and Malay spelling correction features. Obtain your key from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Examples

**1. Perform a Dry Run (Highly Recommended First Step):**
This command will simulate the renaming process and display all proposed changes without altering any files.

```bash
python exif-date-organizer.py /Volumes/MyExternalDrive/PhotosAndVideos
```

**2. Execute Renaming with AI-Powered Corrections:**
This command will apply the renaming changes and leverage the AI model for intelligent text formatting.

```bash
python exif-date-organizer.py /Volumes/MyExternalDrive/PhotosAndVideos --live --ai-api-key YOUR_GOOGLE_AI_API_KEY
```

**3. Live Renaming with Custom Confidence and Specific Casing (without AI):**

```bash
python exif-date-organizer.py C:\Users\MyUser\MediaArchive --live --confidence 0.75 --case upper
```

## Logging

All operations and events are meticulously logged to `exif-date-organizer.log`, located in the same directory as the script. This log file provides a detailed record of renamed folders, skipped folders, and any encountered errors.

## How It Works

The script operates by systematically traversing through each subfolder within the specified target path:

1.  **Metadata Collection:** It scans all image and video files within each subfolder to extract creation date information from their embedded metadata (EXIF for images, `hachoir` for videos).
2.  **Date Analysis:** The collected dates are analyzed to determine the most frequently occurring creation date within the folder.
3.  **Confidence Check:** A confidence score is computed. If this score falls below the user-defined `--confidence` threshold, the folder is safely skipped to avoid unreliable renames.
4.  **Name Preparation:** The original folder name is cleaned by removing any leading date or numerical prefixes.
5.  **AI Enhancement (if enabled):** If an `--ai-api-key` is provided, the cleaned folder name is sent to a Google Generative AI model. The AI processes the name to apply proper title casing, correct Malay spelling, and preserve existing acronyms.
6.  **New Name Construction:** A new, standardized folder name is constructed in the format `YYYY-MM-DD Cleaned Folder Name`.
7.  **Execution or Simulation:** If the `--live` flag is present, the folder is actually renamed. Otherwise, the proposed rename is reported without making any file system modifications (dry run).
8.  **Final Report:** Upon completion, a comprehensive summary report is generated, detailing all renamed, skipped, and error-affected folders.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/N4Z1T/exif-date-organizer/issues) or fork the repository and submit pull requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
