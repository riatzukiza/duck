import React, { useState, useRef, useEffect } from 'react';

function AudioVisualizer({ audioUrl }) {
  const canvasRef = useRef(null);
  const [audioBuffer, setAudioBuffer] = useState(null);

  useEffect(() => {
    if (!audioUrl) return;

    const context = new AudioContext();

    fetch(audioUrl)
      .then(res => res.arrayBuffer())
      .then(buffer => context.decodeAudioData(buffer))
      .then(decoded => {
        setAudioBuffer(decoded);
        drawWaveform(decoded);
      });

    function drawWaveform(buffer) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#444';
      ctx.fillRect(0, 0, width, height);
      ctx.strokeStyle = '#0f0';
      ctx.lineWidth = 1;

      const channelData = buffer.getChannelData(0); // Use first channel

      ctx.beginPath();

      const step = Math.ceil(channelData.length / width);
      for(let i = 0; i < width; i++) {
        const min = Math.min(...channelData.slice(i * step, (i+1)*step));
        const max = Math.max(...channelData.slice(i * step, (i+1)*step));
        ctx.moveTo(i, (1 + min) * height/2);
        ctx.lineTo(i, (1 + max) * height/2);
      }
      ctx.stroke();
    }
  }, [audioUrl]);

  return <canvas ref={canvasRef} width={600} height={150} style={{ border: '1px solid #ddd' }} />;
}

export default AudioVisualizer;
