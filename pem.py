import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
import os
import numpy as np
from io import BytesIO

# For video processing
from moviepy.editor import VideoFileClip, AudioFileClip
from tempfile import NamedTemporaryFile

# Adjust the main content width to fit within the viewport minus 5%
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 95%;
        padding-left: 2.5%;
        padding-right: 2.5%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and Description
st.title("Image and Video Quality Degradation Analysis")
st.write("Upload an image or video to visualize quality degradation using PEM degradation difference analysis.")
st.write("10.6084/m9.figshare.27308148")

# File Upload
uploaded_file = st.file_uploader("Choose an image or video...", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"])

# Toggle for output type
output_type = st.radio("Choose output type:", ('Joined', 'Separate'))

# Main processing function for images
def process_image(image, output_type='Joined'):
    # Convert image to RGB if it has an alpha channel
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    # Save a low-quality temporary image to a BytesIO object
    temp_io = BytesIO()
    image.save(temp_io, "JPEG", quality=5)
    temp_io.seek(0)
    temp_img = Image.open(temp_io)
    
    # Calculate pixel differences
    diff_img = ImageChops.difference(image, temp_img)
    
    # Determine brightness scaling based on pixel differences
    max_diff = max(max(e) for e in diff_img.getextrema())
    scale = 4850.0 / max_diff
    enhanced_img = ImageEnhance.Brightness(diff_img).enhance(scale)
    
    if output_type == 'Joined':
        # Stitch the processed image above the original image
        width, height = image.size
        total_height = height * 2
        stitched_img = Image.new('RGB', (width, total_height))
        stitched_img.paste(enhanced_img, (0, 0))
        stitched_img.paste(image, (0, height))
        return stitched_img
    else:
        # Return processed image separately
        return enhanced_img

# Main processing function for videos
def process_video(video_path, output_type='Joined'):
    # Load the video clip
    clip = VideoFileClip(video_path)
    audio = clip.audio  # Extract audio to re-add it later

    # Process each frame
    def process_frame(frame):
        # Convert frame to PIL Image
        frame_img = Image.fromarray(frame)
        processed_img = process_image(frame_img, output_type)
        # Convert back to numpy array
        return np.array(processed_img)

    # Apply the processing to each frame
    processed_clip = clip.fl_image(process_frame)
    processed_clip = processed_clip.set_audio(audio)

    # Save the processed video to a temporary file
    temp_video_file = NamedTemporaryFile(delete=False, suffix='.mp4')
    
    # Use ffmpeg_params to set encoding profile for compatibility
    processed_clip.write_videofile(
        temp_video_file.name,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        ffmpeg_params=[
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-pix_fmt', 'yuv420p'
        ],
        threads=4
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
        processed_img = process_image(original_img, output_type)
        
        # Display the results based on the chosen output type
        if output_type == 'Joined':
            st.image(processed_img, caption="Processed Image with Original Below", use_column_width=True)
        else:
            st.image(processed_img, caption="Processed Image", use_column_width=True)
            st.image(original_img, caption="Original Image", use_column_width=True)
        
        # Option to download the processed image
        buffered = BytesIO()
        processed_img.save(buffered, format="JPEG")
        btn = st.download_button(
            label="Download Processed Image",
            data=buffered.getvalue(),
            file_name="processed_image.jpg",
            mime="image/jpeg"
        )
    elif file_type.startswith('video/'):
        st.video(uploaded_file)
        st.write("Processing video...")
        
        # Save the uploaded video to a temporary file
        with NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input_file:
            temp_input_file.write(uploaded_file.read())
            temp_input_file.flush()
            processed_video_path = process_video(temp_input_file.name, output_type)
        
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
    else:
        st.error("Unsupported file type.")
