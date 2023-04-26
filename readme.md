# Photoelectromagnetic Analysis (PEMi) Script

This script is designed to perform Photoelectromagnetic Analysis on images or videos. It uses the Python Imaging Library (PIL) and the FFMPEG library to extract frames from videos, apply the PEMI algorithm to the frames, and stitch the processed frames back together to form a new video. It can also process individual images and save the processed image in the same directory as the original.

## Installation

1. Clone or download the script from the [GitHub repository](https://github.com).
2. Install the required dependencies by running the following command:

  ```
pip install argparse Pillow ffmpeg-python
  ```
3. Install FFMPEG on your system using one of the following methods:
- **MacOS**: Run the following command in the terminal:
  ```
  brew install ffmpeg
  ```
- **Windows**: Download the FFMPEG executable from the [official website](https://ffmpeg.org/download.html#build-windows) and add it to your system PATH.
- **Linux**: Run the following command in the terminal:
  ```
  sudo apt-get install ffmpeg
  ```

## Usage

The script can be executed from the command line using the following command:

python pemi.py -i input_path


Where `input_path` is the path to the input file or directory.

### Options

The following command-line options are available:

- `-i`, `--input`: The path to the input file or directory. This option is **required**.
- `-h`, `--help`: Show the help message and exit.

### Supported Formats

The script supports the following input file formats:

- Images: `.png`, `.jpg`, `.jpeg`, `.webp`
- Videos: `.mp4`, `.mov`, `.webm`, `.avi`, `.flv`, `.f4v`, `.mkv`

### Example

To process an image, run the following command:

python pemi.py -i /path/to/image.jpg # {or png, webp, jpeg}

To process a video, run the following command:

python pemi.py -i /path/to/video.mp4

To process all images in a directory, run the following command:

python pemi.py -i /path/to/directory

## Output

Processed images are saved in the same directory as the original image, with the prefix "pemi_" added to the filename. Processed videos are saved in the same directory as the input video, with "_pemi" added to the filename. 

## Cleanup

The script creates a temporary directory (`/tmp/pemi/`) to store intermediate files. This directory is automatically deleted when the script exits. If the script is interrupted or terminated prematurely, the temporary directory may not be deleted. In this case, you can manually delete the directory to free up disk space.
