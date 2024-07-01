from PIL import Image, ImageChops, ImageEnhance
import os

def processImage(imagePath): # absolute core function
    im = Image.open(imagePath)
    tfn = imagePath.replace('.jpg', '.tmp.jpg')
    pfn = imagePath.replace('.jpg', '_pemi.jpg')
    im.save(tfn, "JPEG", quality=5)
    tmi = Image.open(tfn)
    pi = ImageChops.difference(im, tmi)
    md = max(max(e) for e in pi.getextrema())
    s = 4850.0 / md
    pi = ImageEnhance.Brightness(pi).enhance(s)
    pi.save(pfn)
    os.remove(tfn)
