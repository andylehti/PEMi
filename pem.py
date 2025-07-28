import streamlit as st
import streamlit.components.v1 as components
import os
from tempfile import NamedTemporaryFile
from moviepy.editor import VideoFileClip, AudioFileClip
from PIL import Image
import numpy as np
from io import BytesIO

st.title("Image and Video Quality Degradation Analysis")
st.write("Upload an image or video to visualize quality degradation using PEM degradation difference analysis.")
st.write("10.6084/m9.figshare.27308148")

uploaded_file = st.file_uploader("Choose an image or video...", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"])

# Your JavaScript embedded as a string for images:
js_image_processing_html = """
<input type="file" id="upload-image" accept="image/*" />
<br><br>
<canvas id="canvas-original" style="border:1px solid #ddd;"></canvas>
<canvas id="canvas-ida" style="border:1px solid #ddd; margin-left:10px;"></canvas>

<script>
  (function() {
    const uploadInput = document.getElementById('upload-image');
    const canvasOriginal = document.getElementById('canvas-original');
    const canvasIDA = document.getElementById('canvas-ida');
    const ctxOriginal = canvasOriginal.getContext('2d');
    const ctxIDA = canvasIDA.getContext('2d');

    const jpegQuality = 5;
    const gamma = 25;

    let img = new Image();

    function imageToCanvas(img, canvas) {
      canvas.width = img.width;
      canvas.height = img.height;
      let ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
    }

    function recompressImage(canvas, quality, callback) {
      canvas.toBlob(blob => {
        let recompressed = new Image();
        recompressed.onload = () => callback(recompressed);
        recompressed.src = URL.createObjectURL(blob);
      }, 'image/jpeg', quality / 100);
    }

    function computeIDA(originalCanvas, recompressedImg, scale) {
      const width = originalCanvas.width;
      const height = originalCanvas.height;
      canvasIDA.width = width;
      canvasIDA.height = height;

      ctxIDA.drawImage(recompressedImg, 0, 0);
      const originalData = ctxOriginal.getImageData(0, 0, width, height).data;
      const recompressedData = ctxIDA.getImageData(0, 0, width, height);
      const outputData = recompressedData.data;

      for (let i = 0; i < originalData.length; i += 4) {
        outputData[i] = Math.min(Math.abs(originalData[i] - outputData[i]) * scale, 255);
        outputData[i+1] = Math.min(Math.abs(originalData[i+1] - outputData[i+1]) * scale, 255);
        outputData[i+2] = Math.min(Math.abs(originalData[i+2] - outputData[i+2]) * scale, 255);
        outputData[i+3] = 255;
      }

      ctxIDA.putImageData(recompressedData, 0, 0);
    }

    function runIDA() {
      imageToCanvas(img, canvasOriginal);
      recompressImage(canvasOriginal, jpegQuality, recompressed => {
        computeIDA(canvasOriginal, recompressed, gamma);
      });
    }

    uploadInput.addEventListener('change', e => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = event => {
        img.onload = () => runIDA();
        img.src = event.target.result;
      };
      reader.readAsDataURL(file);
    });
  })();
</script>
"""

# Python video processing function (your existing code)
def process_video(video_path):
    clip = VideoFileClip(video_path)
    audio = clip.audio

    def process_frame(frame):
        frame_img = Image.fromarray(frame)
        # Could integrate python image processing here if needed
        return np.array(frame_img)

    processed_clip = clip.fl_image(process_frame)
    processed_clip = processed_clip.set_audio(audio)

    temp_video_file = NamedTemporaryFile(delete=False, suffix='.mp4')
    processed_clip.write_videofile(
        temp_video_file.name,
        codec='libx264',
        audio_codec='aac',
        bitrate='4000k',
        preset='medium',
        threads=4,
        ffmpeg_params=["-movflags", "faststart"]
    )
    return temp_video_file.name

if uploaded_file:
    file_type = uploaded_file.type

    if file_type.startswith("image/"):
        # Inject the JS-based image processor iframe
        # WARNING: This will show a new file input inside iframe, separate from Streamlit uploader
        st.write("Image detected. Use the box below to upload and process your image with JavaScript:")
        components.html(js_image_processing_html, height=600)

    elif file_type.startswith("video/"):
        st.video(uploaded_file)
        st.write("Processing video...")

        with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input_file:
            temp_input_file.write(uploaded_file.read())
            temp_input_file.flush()
            processed_video_path = process_video(temp_input_file.name)

        st.video(processed_video_path)

        with open(processed_video_path, "rb") as file:
            st.download_button(
                label="Download Processed Video",
                data=file,
                file_name="processed_video.mp4",
                mime="video/mp4"
            )

        os.remove(temp_input_file.name)
        os.remove(processed_video_path)

    else:
        st.error("Unsupported file type.")
else:
    st.write("Upload an image or video file above.")
