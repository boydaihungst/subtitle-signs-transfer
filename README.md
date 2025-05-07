# subtitle-signs-transfer

Transfer signs with coresponding styles from one .ass subtitle file to another.

## Installation

### Requirements

- Python >= 3.12
- pip
- git

### Installation

```bash
git clone https://github.com/boydaihungst/subtitle-signs-transfer.git
cd subtitle-signs-transfer
pip install -r requirements.txt
```

You may need to create a virtual environment first. See [here](https://python.land/virtual-environments/virtualenv) to learn how to create one.

## Usage

Activate the virtual environment first. See the link above for more details.

Then, run the following command:

- For single file pair:

  ```bash
  python main.py source.ass target.ass
  ```

- For directory pair:

  ```bash
  python main.py source_directory target_directory
  ```

  The script will automatically find corresponding files in the target directory and perform sign transfer for each pair.
  For example, if there are two files in the `source` directory named `file1.ass` and `file2.ass`, and there are two files in the `target` directory named `file1.ass` and `file2.ass`, the script will perform sign transfer for `file1.ass` and `file2.ass`.
