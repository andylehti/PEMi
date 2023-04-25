#!/usr/bin/env python3

import argparse
import sys
import os
from PIL import Image, ImageChops, ImageEnhance
from concurrent.futures import ThreadPoolExecutor
import subprocess
import tempfile

TMP_EXT = ".tmp.jpg"
PEMI_EXT = ".jpg"
SAVE_REL_DIR = "processed"
quality = 5
accepted_image_formats = (".png", ".jpg", ".jpeg", ".webp")
accepted_video_formats = (".mp4", ".mov", ".webm", ".avi", ".flv", ".f4v", ".mkv")

def extract_frames(input_video, output_dir):
    subprocess.run(["ffmpeg", "-i", input_video, "-q:v", "1", f"{output_dir}/frame%04d.jpg"])

def stitch_frames(input_dir, output_video):
    subprocess.run(
        [
            "ffmpeg",
            "-framerate",
            "30",
            "-i",
            f"{input_dir}/frame%04d.jpg",
            "-c:v",
            "libx265",
            "-crf",
            "0",
            "-preset",
            "veryslow",
            "-pix_fmt",
            "yuv420p",
            output_video,
        ]
    )

def pemi(fname, orig_dir, save_dir):
    basename, ext = os.path.splitext(fname)

    org_fname = os.path.join(orig_dir, fname)
    tmp_fname = os.path.join(save_dir, basename + TMP_EXT)
    pemi_fname = os.path.join(save_dir, "pemi_" + basename + PEMI_EXT)

    im = Image.open(org_fname)
    im.save(tmp_fname, "JPEG", quality=quality)

    tmp_fname_im = Image.open(tmp_fname)
    pemi_im = ImageChops.difference(im, tmp_fname_im)

    extrema = pemi_im.getextrema()
    max_diff = max(max(ex) for ex in extrema)
    scale = 4850.0 / max_diff
    pemi_im = ImageEnhance.Brightness(pemi_im).enhance(scale)
    pemi_im.save(pemi_fname)
    os.remove(tmp_fname)

def install():
    os.system("sudo rm /usr/local/bin/pemi")
    os.system("chmod +x ~/pemi.py")
    os.system("sudo ln -s ~/pemi.py /usr/local/bin/pemi")

def process(input_path):
    if os.path.isfile(input_path):
        input_ext = os.path.splitext(input_path)[1].lower()
        if input_ext in accepted_image_formats:
            input_dir = os.path.dirname(input_path)
            pemi(os.path.basename(input_path), input_dir, input_dir)
            print(f"Processed image saved as pemi_{os.path.basename(input_path)}")
        elif input_ext in accepted_video_formats:
            output_video = os.path.splitext(input_path)[0] + "_pemi.mp4"
            with tempfile.TemporaryDirectory() as tmpdir:
                extract_frames(input_path, tmpdir)
                pemi_dirc = os.path.join(tmpdir, SAVE_REL_DIR)

                if not os.path.exists(pemi_dirc):
                    os.makedirs(pemi_dirc)

                image_files = [d for d in os.listdir(tmpdir) if d.lower().endswith(".jpg")]

                with ThreadPoolExecutor() as executor:
                    for image_file in image_files:
                        executor.submit(pemi, image_file, tmpdir, pemi_dirc)

                stitch_frames(pemi_dirc, output_video)
                print(f"Processed video saved as {output_video}")

        else:
            print(f"Invalid file format for {input_path}. Accepted formats: {accepted_image_formats + accepted_video_formats}")

    elif os.path.isdir(input_path):
        pemi_dirc = os.path.join(input_path, SAVE_REL_DIR)

        if not os.path.exists(pemi_dirc):
            os.makedirs(pemi_dirc)

        image_files = [
            d for d in os.listdir(input_path) if d.lower().endswith(accepted_image_formats)
        ]

        with ThreadPoolExecutor() as executor:
            for image_file in image_files:
                executor.submit(pemi, image_file, input_path, pemi_dirc)

        print("Finished processing images!")
        print(f"Processed images saved in {pemi_dirc}")

    else:
        print("Invalid input path. Please provide a valid file or directory path.")

def main():
    parser = argparse.ArgumentParser(description="Performs Photoelectromagnetic Analysis on images or video.")
    parser.add_argument("-i", "--input", dest="input_path", required=True, help="Input file or directory")
    parser.add_argument("--install", action="store_true", help="Install or reinstall the script to the system")

    args = parser.parse_args()

    if args.install:
        install()
        print("The script has been installed/reinstalled successfully")
    else:
        process(args.input_path)

if __name__ == "__main__":
    main()
