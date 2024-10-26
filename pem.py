import streamlit as st
from PIL import Image, ImageChops, ImageEnhance
import os

# Title and Description
st.title("Image Quality Degradation Analysis")
st.write("Upload an image to visualize quality degradation using PEM degradation difference image analysis.")

# Image Upload
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Main processing function
def process_image(image):
    # Convert image to RGB if it has an alpha channel
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    tfn = "temp_image.tmp.jpg"
    pfn = "processed_image_pem.jpg"
    
    # Save a low-quality temporary image
    image.save(tfn, "JPEG", quality=5)
    temp_img = Image.open(tfn)
    
    # Calculate pixel differences
    diff_img = ImageChops.difference(image, temp_img)
    
    # Determine brightness scaling based on pixel differences
    max_diff = max(max(e) for e in diff_img.getextrema())
    scale = 4850.0 / max_diff
    enhanced_img = ImageEnhance.Brightness(diff_img).enhance(scale)
    
    # Save and return the processed image
    enhanced_img.save(pfn)
    os.remove(tfn)
    return enhanced_img

# Process the uploaded image if provided
if uploaded_file:
    original_img = Image.open(uploaded_file)
    
    # Display Original Image
    st.image(original_img, caption="Original Image", use_column_width=True)
    
    # Process and display PEM-style difference image
    st.write("Processing image...")
    processed_img = process_image(original_img)
    st.image(processed_img, caption="PEM-style Difference Image", use_column_width=True)
    
    # Option to download the processed image
    with open("processed_image_pem.jpg", "rb") as file:
        btn = st.download_button(
            label="Download Processed Image",
            data=file,
            file_name="PEM_difference_image.jpg",
            mime="image/jpeg"
        )
