import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
import os
import numpy as np
from io import BytesIO
import subprocess
import json

# For video processing
from moviepy.editor import VideoFileClip, AudioFileClip
from tempfile import NamedTemporaryFile

# Function to extract video bitrate using ffprobe
def get_video_bitrate(video_path):
    """
    Extracts the video and audio bitrate using ffprobe.

    Args:
        video_path (str): Path to the video file.

    Returns:
        dict: A dictionary containing video and audio bitrate in kbps.
    """
    try:
        # Run ffprobe command to get bitrate information in JSON format
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'format=bit_rate',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        video_info = json.loads(result.stdout)
        video_bitrate = int(video_info['format']['bit_rate']) // 1000  # Convert to kbps

        # Extract audio bitrate
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'format=bit_rate',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        audio_info = json.loads(result.stdout)
        audio_bitrate = int(audio_info['format']['bit_rate']) // 1000  # Convert to kbps

        return {'video_bitrate': video_bitrate, 'audio_bitrate': audio_bitrate}
    except Exception as e:
        st.error(f"Error extracting bitrate: {e}")
        return {'video_bitrate': '4000k', 'audio_bitrate': '128k'}  # Fallback values

# Title and Description
st.title("Image and Video Quality Degradation Analysis")
st.write("Upload an image or video to visualize quality degradation using PEM degradation difference analysis.")
st.write("Reference: [10.6084/m9.figshare.27308148](https://doi.org/10.6084/m9.figshare.27308148)")

# File Upload
uploaded_file = st.file_uploader("Choose an image or video...", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"])

# Main processing function for images
def process_image(image):
    # Convert image to RGB if it has an alpha channel
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    # Ensure no resizing before processing

    # Save a low-quality temporary image to a BytesIO object for difference calculation
    temp_io = BytesIO()
    image.save(temp_io, "JPEG", quality=5)  # Low quality for difference calculation
    temp_io.seek(0)
    temp_img = Image.open(temp_io)
    
    # Calculate pixel differences
    diff_img = ImageChops.difference(image, temp_img)
    
    # Determine brightness scaling based on pixel differences
    max_diff = max(max(e) for e in diff_img.getextrema())
    if max_diff == 0:
        scale = 1  # Avoid division by zero
    else:
        scale = 4850.0 / max_diff
    enhanced_img = ImageEnhance.Brightness(diff_img).enhance(scale)
    
    # Decide whether to stack vertically or side by side based on image dimensions
    width, height = image.size
    if height > width:
        # Stack side by side
        total_width = width * 2
        stitched_img = Image.new('RGB', (total_width, height))
        stitched_img.paste(enhanced_img, (0, 0))
        stitched_img.paste(image, (width, 0))
    else:
        # Stack vertically
        total_height = height * 2
        stitched_img = Image.new('RGB', (width, total_height))
        stitched_img.paste(enhanced_img, (0, 0))
        stitched_img.paste(image, (0, height))
    
    return stitched_img

# Main processing function for videos
def process_video(video_path, original_bitrate):
    # Load the video clip
    clip = VideoFileClip(video_path)
    audio = clip.audio  # Extract audio to re-add it later

    # Process each frame
    def process_frame(frame):
        # Convert frame to PIL Image
        frame_img = Image.fromarray(frame)
        processed_img = process_image(frame_img)
        # Convert back to numpy array
        return np.array(processed_img)
    
    # Apply the processing to each frame
    processed_clip = clip.fl_image(process_frame)
    processed_clip = processed_clip.set_audio(audio)
    
    # Save the processed video to a temporary file with original bitrate
    temp_video_file = NamedTemporaryFile(delete=False, suffix='.mp4')
    processed_clip.write_videofile(
        temp_video_file.name,
        codec='libx264',
        audio_codec='aac',
        bitrate=f"{original_bitrate['video_bitrate']}k",  # Match original video bitrate
        audio_bitrate=f"{original_bitrate['audio_bitrate']}k",  # Match original audio bitrate
        preset='medium',    # Adjust encoding speed vs compression
        threads=4,          # Utilize multiple threads for faster encoding
        ffmpeg_params=["-movflags", "faststart"]  # Optimize for web streaming
    )

    return temp_video_file.name

# Process the uploaded file if provided
if uploaded_file:
    file_type = uploaded_file.type
    if file_type.startswith('image/'):
        original_img = Image.open(uploaded_file)
        
        # Display Original Image
        st.image(original_img, caption="Original Image", use_column_width=True)
        
        # Process and display PEM-style difference image
        st.write("Processing image...")
        processed_img = process_image(original_img)
        st.image(processed_img, caption="Processed Image with Original", use_column_width=True)
        
        # Option to download the processed image as PNG
        buffered = BytesIO()
        processed_img.save(buffered, format="PNG", optimize=True)
        buffered.seek(0)  # Ensure buffer is at the start
        btn = st.download_button(
            label="Download Processed Image",
            data=buffered,
            file_name="processed_image.png",
            mime="image/png"
        )
    elif file_type.startswith('video/'):
        st.video(uploaded_file)
        st.write("Processing video...")
        
        # Save the uploaded video to a temporary file
        with NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input_file:
            temp_input_file.write(uploaded_file.read())
            temp_input_file.flush()
            temp_input_file_path = temp_input_file.name
        
        # Extract original bitrate
        original_bitrate = get_video_bitrate(temp_input_file_path)
        
        # Process the video
        processed_video_path = process_video(temp_input_file_path, original_bitrate)
        
        # Display the processed video
        st.video(processed_video_path)
        
        # Option to download the processed video
        with open(processed_video_path, "rb") as file:
            btn = st.download_button(
                label="Download Processed Video",
                data=file,
                file_name="processed_video.mp4",
                mime="video/mp4"
            )
        
        # Delete temporary files after processing
        try:
            os.remove(temp_input_file_path)
            os.remove(processed_video_path)
        except Exception as e:
            st.warning(f"Could not delete temporary files: {e}")
    else:
        st.error("Unsupported file type.")
