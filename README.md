# subtitle-signs-transfer

Transfer signs with coresponding styles from one .ass subtitle file to another.

## Installation

### Requirements

- Python >= 3.12
- pip
- git
- aegisub + [aegisub-cli](https://github.com/HengXin666/aegisub-cli) (Optional) to resample the subtitles to specific video resolution, before transferring signs.

### Installation

```bash
git clone https://github.com/boydaihungst/subtitle-signs-transfer.git
cd subtitle-signs-transfer
pip install -r requirements.txt
```

You may need to create a virtual environment first. See [here](https://python.land/virtual-environments/virtualenv) to learn how to create one.

## Usage

Activate the virtual environment first. See the link above for more details.

```sh
usage: main.py [-h] [-a AEGISUBCLI] [-s [EXTRA_EXCLUDED_TAGS ...]] source target

Transfer signs from one .ass subtitle file(s) to another.

positional arguments:
  source                Path to the source .ass file or source directory.
  target                Path to the target .ass file or target directory.

options:
  -h, --help            show this help message and exit
  -a, --aegisubcli /path/to/aegisub-cli
                        Path to the aegisub-cli tool. Defaults to searching for
                        aegisub-cli in the PATH environment variable.
  -s, --skip-tags [EXTRA_EXCLUDED_TAGS ...]
                        .ASS extra tags to skip (without backslash). These tags
                        will be 'skipped' before checking whether the line has
                        special tags or not.
                        Example: skip \i (italic) or \pos tags lines '-s pos i'
                        these tags will add to the default skipped tags
                        (\N \be \fe \r \b \bord \q \u \s).
```

Then, run the following command:

- For single file pair:

  ```bash
  python main.py source.ass target.ass

  # or if you have aegisub-cli installed in custom path and want to use it for resampling subtitles to target resolution automatically.
  python main.py source.ass target.ass -a /path/to/aegisub-cli

  # extra tags to skip (without backslash). These tags will be 'skipped' before checking whether the line has special tags or not.
  # Example: skip \i (italic) or \pos tags lines '-s pos i' these tags will add to the default skip tags (\N \be \fe \r \b \bord \q \u \s).
  python main.py source.ass target.ass --skip-tags i
  ```

- For directory pair:

  ```bash
  python main.py source_directory target_directory

  # or if you have aegisub-cli installed in custom path and want to use it for resampling subtitles to target resolution automatically.
  python main.py source_directory target_directory -a /path/to/aegisub-cli

  # extra tags to skip (without backslash). These tags will be 'skipped' before checking whether the line has special tags or not.
  # Example: skip \i (italic) or \pos tags lines '-s pos i' these tags will add to the default skipped tags (\N \be \fe \r \b \bord \q \u \s).
  python main.py source_directory target_directory -s pos i
  ```

  The script will automatically find corresponding files in the target directory and perform sign transfer for each pair.
  For example, if there are two files in the `source` directory named `file1.ass` and `file2.ass`, and there are two files in the `target` directory named `file1.ass` and `file2.ass`, the script will perform sign transfer for `file1.ass` and `file2.ass`.
