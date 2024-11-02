import os
from PIL import Image, ImageChops, ImageEnhance
from io import BytesIO

def convertJpeg(path):
    with Image.open(path) as img:
        jpegPath = f"{os.path.splitext(path)[0]}.jpg"
        rgb_img = img.convert('RGB') if img.mode != 'RGB' else img
        rgb_img.save(jpegPath, "JPEG")
    return jpegPath

def processImg(img, m, x):
    if img.mode == 'RGBA': img = img.convert('RGB')
    tempIo = BytesIO(); img.save(tempIo, "JPEG", quality=min(10, x)); tempIo.seek(0)
    tempImg = Image.open(tempIo)
    diff = ImageChops.difference(img, tempImg)
    maxDiff = max(max(e) for e in diff.getextrema()) or 1
    enhanced = ImageEnhance.Brightness(diff).enhance(m / maxDiff)
    return enhanced

def stitchImage(img, enhanced):
    width, height = img.size
    if height > width:
        stitched = Image.new('RGB', (width * 2, height))
        stitched.paste(enhanced, (0, 0))
        stitched.paste(img, (width, 0))
    else:
        stitched = Image.new('RGB', (width, height * 2))
        stitched.paste(enhanced, (0, 0))
        stitched.paste(img, (0, height))
    return stitched

def processImage(path, outPath, m, x, y):
    with Image.open(path) as img:
        enhanced = processImg(img, m, x)
        processed = stitchImage(img, enhanced) if y == 1 else enhanced
        processed.save(outPath)

def processFile(path, k=0, m=5, x=5, y=0):
    m = 5 if m > 5 else abs(int(m))
    x = 10 if x > 10 else abs(int(x))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Invalid file path: {path}")
    name, ext = os.path.splitext(path)
    n = str(name.split('/')[-1])
    ext = ext.lower()
    if ext not in ['.jpg', '.jpeg', '.png']: path, ext = convertJpeg(path), '.jpg'
    if not os.path.exists(n):
        os.makedirs(n)
    d = os.path.abspath(n)
    outPath = f"{d}/{n}-{m}+{x}{ext}" if k == 0 else f"{d}/{str(k).zfill(5)}_{n}-{m}+{x}{ext}"
    processImage(path, outPath, m * 20 * 50, x, y)

i = '/content/final.jpg'
frame = 0
magnitude = 5
index = 5
combine = 0
processFile(i, frame, magnitude, index, combine)
