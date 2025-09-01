document.addEventListener('DOMContentLoaded', () => {
    const { createFFmpeg, fetchFile } = FFmpeg;
    const ffmpeg = createFFmpeg({
      log: false,
      corePath: 'https://unpkg.com/@ffmpeg/core@0.12.6/dist/ffmpeg-core.js',
    });
  
const fileInput = document.getElementById('fileInput');
const mInput = document.getElementById('mInput');
const xInput = document.getElementById('xInput');
const mVal = document.getElementById('mVal');
const xVal = document.getElementById('xVal');
const detailsCheck = document.getElementById('detailsCheck');
const processBtn = document.getElementById('processBtn');
const gridBtn = document.getElementById('gridBtn');
const standardBtn = document.getElementById('standardBtn');
const saveBtn = document.getElementById('saveBtn');
const compileBtn = document.getElementById('compileBtn');
const darkModeToggle = document.getElementById('darkModeToggle');
const resultCanvas = document.getElementById('resultCanvas');
const dropArea = document.getElementById('drop-area');
const processingIndicatorContainer = document.getElementById('processing-indicator-container');
const processingText = document.getElementById('processingText');
const progressBar = document.getElementById('progressBar');
const rCtx = resultCanvas.getContext('2d');

let loadedFile = null;
let originalFileName = '';
let processedFrames = [];
let isVideo = false;

mInput.addEventListener('input', () => { mVal.textContent = mInput.value; });
xInput.addEventListener('input', () => { xVal.textContent = xInput.value; });

function setProcessingState(isProcessing, message = 'Processing...') {
  const buttons = [processBtn, gridBtn, standardBtn, saveBtn, compileBtn];
  if (isProcessing) {
    processingText.textContent = message;
    processingIndicatorContainer.classList.remove('hidden');
    buttons.forEach(btn => {
      btn.disabled = true;
      btn.classList.add('button-disabled');
    });
  } else {
    processingIndicatorContainer.classList.add('hidden');
    buttons.forEach(btn => {
      btn.disabled = false;
      btn.classList.remove('button-disabled');
    });
  }
}

fileInput.addEventListener('change', async e => {
  const files = e.target.files;
  if (!files.length) return;
  loadedFile = files[0];
  originalFileName = loadedFile.name.split('.').slice(0, -1).join('.');
  
  if (loadedFile.type.startsWith('image/')) {
    isVideo = false;
    processBtn.textContent = 'Process Image';
    saveBtn.textContent = 'Save';
    compileBtn.classList.add('hidden');
    await processImageFile(loadedFile);
  } else if (loadedFile.type.startsWith('video/')) {
    isVideo = true;
    processBtn.textContent = 'Process Video';
    saveBtn.textContent = 'Save Frames';
    compileBtn.classList.add('hidden');
    setProcessingState(false);
  } else {
    setProcessingState(false);
  }
});

dropArea.addEventListener('dragover', e => {
  e.preventDefault();
  dropArea.classList.add('drag-over');
});

dropArea.addEventListener('dragleave', e => {
  dropArea.classList.remove('drag-over');
});

dropArea.addEventListener('drop', async e => {
  e.preventDefault();
  dropArea.classList.remove('drag-over');
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    loadedFile = files[0];
    originalFileName = loadedFile.name.split('.').slice(0, -1).join('.');
    if (loadedFile.type.startsWith('image/')) {
      isVideo = false;
      processBtn.textContent = 'Process Image';
      saveBtn.textContent = 'Save';
      compileBtn.classList.add('hidden');
      await processImageFile(loadedFile);
    } else if (loadedFile.type.startsWith('video/')) {
      isVideo = true;
      processBtn.textContent = 'Process Video';
      saveBtn.textContent = 'Save Frames';
      compileBtn.classList.add('hidden');
      setProcessingState(false);
    } else {
      setProcessingState(false);
    }
  }
});

processBtn.addEventListener('click', async () => {
  if (!loadedFile) return;
  if (isVideo) {
    await processVideoFile(loadedFile);
  } else {
    await processImageFile(loadedFile);
  }
});

gridBtn.addEventListener('click', async () => {
    if (!loadedFile || isVideo) return;
    setProcessingState(true, 'Creating Grid...');
    let mValNum = clampInt(parseInt(mInput.value), 1, 5);
    let showDetails = detailsCheck.checked;
    const resultCanvases = [];
    const img = new Image();
    img.src = URL.createObjectURL(loadedFile);
    
    img.onload = async () => {
        for (let x = 1; x <= 10; x++) {
            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            tempCanvas.width = img.width;
            tempCanvas.height = img.height;
            tempCtx.drawImage(img, 0, 0);
            const processedCanvas = await new Promise(resolve => {
                processFile(tempCanvas, mValNum, x, 'none', showDetails, resolve);
            });
            resultCanvases.push({ canvas: processedCanvas, xValue: x });
        }
        const gridCanvas = document.createElement('canvas');
        const gridCtx = gridCanvas.getContext('2d');
        const itemWidth = img.width;
        const itemHeight = img.height;
        gridCanvas.width = itemWidth * 5;
        gridCanvas.height = itemHeight * 2;
        
        for (let i = 0; i < resultCanvases.length; i++) {
            const row = Math.floor(i / 5);
            const col = i % 5;
            const canvasData = resultCanvases[i].canvas;
            const xVal = resultCanvases[i].xValue;
            gridCtx.drawImage(canvasData, col * itemWidth, row * itemHeight);
            if (showDetails) {
                const text = `m=${mValNum}, x=${xVal}`;
                const padding = 10;
                gridCtx.font = `8px 'Courier New', Courier, monospace`;
                gridCtx.fillStyle = 'white';
                gridCtx.lineWidth = 2;
                gridCtx.strokeStyle = 'black';
                const textX = col * itemWidth + padding;
                const textY = row * itemHeight + itemHeight - padding;
                gridCtx.strokeText(text, textX, textY);
                gridCtx.fillText(text, textX, textY);
            }
        }
        drawResult(gridCanvas);
        setProcessingState(false);
    };
});

standardBtn.addEventListener('click', async () => {
  if (!loadedFile || isVideo) return;
  setProcessingState(true);
  mInput.value = 3;
  xInput.value = 5;
  mVal.textContent = 3;
  xVal.textContent = 5;
  await processImageFile(loadedFile);
});

saveBtn.addEventListener('click', async () => {
  if (!loadedFile) return;
  if (isVideo) {
    const zip = new JSZip();
    processedFrames.forEach((frame, index) => {
      const dataURL = frame;
      const base64 = dataURL.split(',')[1];
      zip.file(`${originalFileName}_frame_${String(index+1).padStart(4, '0')}.png`, base64, { base64: true });
    });
    zip.generateAsync({ type: "blob" }).then(content => {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(content);
      link.download = `${originalFileName}_processed_frames.zip`;
      link.click();
    });
  } else {
    const dataURL = resultCanvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.href = dataURL;
    link.download = `${originalFileName}_IDA.png`;
    link.click();
  }
});

compileBtn.addEventListener('click', async () => {
    if (!loadedFile || !isVideo || processedFrames.length === 0) return;
    await compileVideo(loadedFile);
});

darkModeToggle.addEventListener('click', () => {
  document.documentElement.classList.toggle('dark');
  const isDark = document.documentElement.classList.contains('dark');
  const icon = document.getElementById('darkModeIcon');
  if (isDark) {
    icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.354 5.354l-.707.707M6.346 6.346l-.707-.707m12.728 0l-.707.707M6.346 17.654l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>`;
  } else {
    icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>`;
  }
});

async function processImageFile(file) {
  setProcessingState(true);
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => {
      resultCanvas.width = img.width;
      resultCanvas.height = img.height;
      rCtx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
      rCtx.drawImage(img, 0, 0);
      const mValNum = clampInt(parseInt(mInput.value), 1, 5);
      const xValNum = clampInt(parseInt(xInput.value), 1, 10);
      const stitchDirection = document.querySelector('input[name="stitchDirection"]:checked').value;
      const showDetails = detailsCheck.checked;
      processFile(img, mValNum, xValNum, stitchDirection, showDetails, finalCanvas => {
        drawResult(finalCanvas, mValNum, xValNum, showDetails, 0, 0);
        setProcessingState(false);
        resolve();
      });
    };
    img.src = URL.createObjectURL(file);
  });
}

async function processVideoFile(file) {
  setProcessingState(true, 'Extracting frames...');
  processedFrames = [];
  const video = document.createElement('video');
  video.src = URL.createObjectURL(file);
  video.muted = true;
  video.preload = 'metadata';
  video.crossOrigin = 'anonymous';

  await new Promise(resolve => {
    video.onloadedmetadata = () => resolve();
  });

  const frameCanvas = document.createElement('canvas');
  const frameCtx = frameCanvas.getContext('2d');
  frameCanvas.width = video.videoWidth;
  frameCanvas.height = video.videoHeight;
  resultCanvas.width = video.videoWidth;
  resultCanvas.height = video.videoHeight;
  
  const fps = 30; // Assuming 30 FPS for extraction
  const step = 1 / fps;
  let time = 0;
  const extractedFrames = [];
  
  while (time < video.duration) {
    video.currentTime = time;
    await new Promise(resolve => {
      video.onseeked = () => resolve();
    });
    frameCtx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
    extractedFrames.push(frameCanvas.toDataURL('image/png'));
    time += step;
  }
  
  processedFrames = [];
  const mValNum = clampInt(parseInt(mInput.value), 1, 5);
  const xValNum = clampInt(parseInt(xInput.value), 1, 10);
  const stitchDirection = document.querySelector('input[name="stitchDirection"]:checked').value;
  const showDetails = detailsCheck.checked;

  for (let i = 0; i < extractedFrames.length; i++) {
    if (i % 13 === 0) {
      const percent = Math.floor((i / extractedFrames.length) * 100);
      progressBar.style.width = `${percent}%`;
      processingText.textContent = `Processing frame ${i + 1} of ${extractedFrames.length}...`;
    }
    const img = new Image();
    img.src = extractedFrames[i];
    await new Promise(resolve => {
        img.onload = () => {
            processFile(img, mValNum, xValNum, stitchDirection, showDetails, processedFrameCanvas => {
                processedFrames.push(processedFrameCanvas.toDataURL('image/png'));
                drawResult(processedFrameCanvas);
                resolve();
            });
        }
    });
  }
  
  progressBar.style.width = `100%`;
  processingText.textContent = `Processing complete!`;
  compileBtn.classList.remove('hidden');
  setTimeout(() => setProcessingState(false), 500);
}

function processFile(imgElem, m, x, stitchDirection, showDetails, callback) {
  let scaleFactor = m * (x * 5) * 50;
  let quality = Math.min(10, x);
  compressImage(imgElem, quality, compImg => {
    let diffCanvas = createDiff(imgElem, compImg, scaleFactor);
    let finalCanvas;
    let originalWidth = imgElem.width;
    let originalHeight = imgElem.height;
    let originalImageX = 0;
    let originalImageY = 0;
    if (stitchDirection === 'none') {
        finalCanvas = diffCanvas;
        originalImageX = 0;
        originalImageY = 0;
    } else {
        finalCanvas = stitchImage(imgElem, diffCanvas, stitchDirection);
        switch(stitchDirection) {
            case 'left':
                originalImageX = originalWidth;
                break;
            case 'right':
                originalImageX = 0;
                break;
            case 'top':
                originalImageY = originalHeight;
                break;
            case 'bottom':
                originalImageY = 0;
                break;
        }
    }
    if (callback) {
        callback(finalCanvas);
    } else {
        drawResult(finalCanvas, m, x, showDetails, originalImageX, originalImageY);
        setProcessingState(false);
    }
  });
}

function compressImage(imgElem, q, callback) {
  let w = imgElem.width, h = imgElem.height;
  let tempCanvas = document.createElement('canvas');
  tempCanvas.width = w; 
  tempCanvas.height = h;
  let tCtx = tempCanvas.getContext('2d');
  tCtx.drawImage(imgElem, 0, 0);
  let data = tempCanvas.toDataURL('image/jpeg', q * 0.01);
  let cImg = new Image();
  cImg.onload = () => callback(cImg);
  cImg.src = data;
}

function createDiff(orig, comp, sFactor) {
  let w = orig.width, h = orig.height;
  let oCanvas = document.createElement('canvas');
  oCanvas.width = w; 
  oCanvas.height = h;
  let oCtx = oCanvas.getContext('2d');
  oCtx.drawImage(orig, 0, 0);
  let oData = oCtx.getImageData(0, 0, w, h);
  let cCanvas = document.createElement('canvas');
  cCanvas.width = w; 
  cCanvas.height = h;
  let cCtx = cCanvas.getContext('2d');
  cCtx.drawImage(comp, 0, 0);
  let cData = cCtx.getImageData(0, 0, w, h);
  let dCanvas = document.createElement('canvas');
  dCanvas.width = w; 
  dCanvas.height = h;
  let dCtx = dCanvas.getContext('2d');
  let diffData = dCtx.createImageData(w, h);
  let oArr = oData.data;
  let cArr = cData.data;
  let dArr = diffData.data;
  let maxDiff = 0;
  for (let i = 0; i < oArr.length; i += 4) {
    let r = Math.abs(oArr[i] - cArr[i]);
    let g = Math.abs(oArr[i + 1] - cArr[i + 1]);
    let b = Math.abs(oArr[i + 2] - cArr[i + 2]);
    maxDiff = Math.max(maxDiff, r, g, b);
  }
  if (maxDiff < 1) maxDiff = 1;
  let scale = sFactor / maxDiff;
  for (let i = 0; i < oArr.length; i += 4) {
    let r = Math.abs(oArr[i] - cArr[i]) * scale;
    let g = Math.abs(oArr[i + 1] - cArr[i + 1]) * scale;
    let b = Math.abs(oArr[i + 2] - cArr[i + 2]) * scale;
    dArr[i] = clamp(r, 0, 255);
    dArr[i+1] = clamp(g, 0, 255);
    dArr[i+2] = clamp(b, 0, 255);
    dArr[i+3] = 255;
  }
  dCtx.putImageData(diffData, 0, 0);
  return dCanvas;
}

function stitchImage(orig, diff, direction) {
  let w = orig.width, h = orig.height;
  let finalCanvas = document.createElement('canvas');
  let fCtx = finalCanvas.getContext('2d');
  switch(direction) {
      case 'left':
          finalCanvas.width = w * 2;
          finalCanvas.height = h;
          fCtx.drawImage(diff, 0, 0);
          fCtx.drawImage(orig, w, 0);
          break;
      case 'right':
          finalCanvas.width = w * 2;
          finalCanvas.height = h;
          fCtx.drawImage(orig, 0, 0);
          fCtx.drawImage(diff, w, 0);
          break;
      case 'top':
          finalCanvas.width = w;
          finalCanvas.height = h * 2;
          fCtx.drawImage(diff, 0, 0);
          fCtx.drawImage(orig, 0, h);
          break;
      case 'bottom':
          finalCanvas.width = w;
          finalCanvas.height = h * 2;
          fCtx.drawImage(orig, 0, 0);
          fCtx.drawImage(diff, 0, h);
          break;
  }
  return finalCanvas;
}

function drawResult(canvasElem, m = null, x = null, showDetails = null, originalImageX = 0, originalImageY = 0) {
  if (canvasElem) {
    resultCanvas.width = canvasElem.width;
    resultCanvas.height = canvasElem.height;
    rCtx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
    rCtx.drawImage(canvasElem, 0, 0);
  }
  if (showDetails && m !== null && x !== null) {
    const text = `m=${m}, x=${x}`;
    const padding = 10;
    rCtx.font = `8px 'Courier New', Courier, monospace`;
    rCtx.fillStyle = 'white';
    rCtx.lineWidth = 2;
    rCtx.strokeStyle = 'black';
    const textX = originalImageX + padding;
    const textY = originalImageY + loadedFile.height - padding;
    rCtx.strokeText(text, textX, textY);
    rCtx.fillText(text, textX, textY);
  }
}

function clamp(val, mn, mx) {
  return val < mn ? mn : val > mx ? mx : val;
}

function clampInt(val, mn, mx) {
  let v = Math.floor(Math.abs(val));
  return v < mn ? mn : v > mx ? mx : v;
}

async function compileVideo(originalFile) {
    setProcessingState(true, 'Loading FFmpeg...');
    if (!ffmpeg.isLoaded()) {
        await ffmpeg.load();
    }
    
    setProcessingState(true, 'Writing files to FFmpeg...');
    // Write original video to FFmpeg's virtual file system
    ffmpeg.FS('writeFile', 'input.mp4', await fetchFile(originalFile));
    // Write each processed frame as an image sequence
    for (let i = 0; i < processedFrames.length; i++) {
        const frameData = processedFrames[i].split(',')[1];
        const filename = `frame_${String(i).padStart(4, '0')}.png`;
        ffmpeg.FS('writeFile', filename, await fetchFile(new Blob([Uint8Array.from(atob(frameData), c => c.charCodeAt(0))])));
    }

    setProcessingState(true, 'Compiling video...');
    // Run FFmpeg to create a new video from the processed frames and original audio
    await ffmpeg.run(
        '-framerate', '30', 
        '-i', 'frame_%04d.png',
        '-i', 'input.mp4',
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-map', '0:v:0',
        '-map', '1:a:0?', // Map audio stream if it exists
        '-pix_fmt', 'yuv420p',
        'output.mp4'
    );
    
    setProcessingState(true, 'Creating download link...');
    const data = ffmpeg.FS('readFile', 'output.mp4');
    const blob = new Blob([data.buffer], { type: 'video/mp4' });
    const videoURL = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = videoURL;
    link.download = `${originalFileName}_processed.mp4`;
    link.click();
    
    // Cleanup the virtual file system
    ffmpeg.FS('unlink', 'input.mp4');
    for (let i = 0; i < processedFrames.length; i++) {
        const filename = `frame_${String(i).padStart(4, '0')}.png`;
        ffmpeg.FS('unlink', filename);
    }
    
    setTimeout(() => setProcessingState(false), 500);
}
