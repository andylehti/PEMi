import argparse
import sys
import os
from PIL import Image, ImageChops, ImageEnhance
from concurrent.futures import ThreadPoolExecutor
import subprocess
import tempfile
import atexit
import shutil

def cleanup():
    shutil.rmtree('/tmp/pemi/')

atexit.register(cleanup)


TMP_EXT = ".tmp.jpg"
PEMI_EXT = ".jpg"
SAVE_REL_DIR = "processed"
FRAME_RATE = 30  # or any desired frame rate value
OUTPUT_DIR = "/tmp/pemi" #as tempdir
quality = 5
accepted_image_formats = (".png", ".jpg", ".jpeg", ".webp")
accepted_video_formats = (".mp4", ".mov", ".webm", ".avi", ".flv", ".f4v", ".mkv")


def extract_frames(input_video, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cmd = f"ffmpeg -i '{input_video}' -vf 'scale=1920:-2' '{output_dir}/tf_%07d.jpg'"
    os.system(cmd)


def stitch_frames(input_dir, output_video):
    input_pattern = os.path.join(input_dir, "pemi_tf_1%07d.jpg")
    cmd = (
        f"ffmpeg -y -framerate {FRAME_RATE} -pattern_type glob -i '{input_pattern}' "
        f"-c:v libx264 -profile:v high -crf 1 -pix_fmt yuv420p "
        f"-vf 'copy' './(input_video)'"
    )
    os.system(cmd)


    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while stitching frames: {e}")
        raise


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

def process(input_path):
    if os.path.isfile(input_path):
        input_ext = os.path.splitext(input_path)[1].lower()
        if input_ext in accepted_image_formats:
            input_dir = os.path.dirname(input_path)
            pemi(os.path.basename(input_path), input_dir, input_dir)
            print(f"Processed image saved as pemi_{os.path.basename(input_path)}")
        elif input_ext in accepted_video_formats:
            output_video = os.path.splitext(input_path)[0] + "_pemi.mp4"

            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            extract_frames(input_path, OUTPUT_DIR)
            pemi_dirc = os.path.join(OUTPUT_DIR, SAVE_REL_DIR)

            if not os.path.exists(pemi_dirc):
                os.makedirs(pemi_dirc)

            image_files = [d for d in os.listdir(OUTPUT_DIR) if d.lower().endswith(".jpg")]

            with ThreadPoolExecutor() as executor:
                for image_file in image_files:
                    executor.submit(pemi, image_file, OUTPUT_DIR, pemi_dirc)

            stitch_frames(pemi_dirc, output_video)
            print(f"Processed video saved as {output_video}")

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

    args = parser.parse_args()

    process(args.input_path)

    atexit.register(cleanup)

if __name__ == "__main__":
    main()
