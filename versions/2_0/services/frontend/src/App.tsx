import React, { useState } from "react";
import { Button, Slider, TextField, Typography, Card, CardContent } from "@mui/material";
import decodeAudio from 'audio-decode';
import AudioVisualizer from "./AudioVisualizer";


async function fetchAndStripWavHeader(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to fetch audio file: ${response.statusText}`);
    }
    const arrayBuffer = await response.arrayBuffer();
    if (arrayBuffer.byteLength <= 44) {
        throw new Error("Audio file too short to be valid WAV");
    }
    // Slice off the first 44 bytes (WAV header)
    return arrayBuffer.slice(43);
}

async function fetchAndDecodeWav(url: string) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to fetch audio file: ${response.statusText}`);
    }
    const arrayBuffer = await response.arrayBuffer();

    const audioBuffer = await decodeAudio(arrayBuffer);

    function interleaveChannels(audioBuffer) {
        const numChannels = audioBuffer.numberOfChannels;
        const length = audioBuffer.length;
        const interleaved = new Float32Array(length * numChannels);

        for (let i = 0; i < length; i++) {
            for (let ch = 0; ch < numChannels; ch++) {
                interleaved[i * numChannels + ch] = audioBuffer.getChannelData(ch)[i];
            }
        }
        return interleaved;
    }

    const interleavedFloat32 = interleaveChannels(audioBuffer);

    // Now convert Float32Array [-1..1] to Int16Array PCM:
    function floatTo16BitPCM(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            let s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array;
    }
    return floatTo16BitPCM(interleavedFloat32);

}

export default function AudioEQTuner() {
  const [highpass, setHighpass] = useState(90);
  const [lowpass, setLowpass] = useState(6200);
  const [notch1, setNotch1] = useState([200, 300]);
  const [notch2, setNotch2] = useState([320, 460]);
  const [boost, setBoost] = useState([3000, 4000]);
  const [transcription, setTranscription] = useState("");
  const [loading, setLoading] = useState(false);

  const sendRequest = async () => {
    setLoading(true);
    setTranscription("");
    const query = new URLSearchParams({
      highpass: highpass.toString(),
      lowpass: lowpass.toString(),
      notch1: notch1.join("-"),
      notch2: notch2.join("-"),
      boost: boost.join("-"),
    });

    const response = await fetch(
      `http://localhost:5001/transcribe_pcm/equalized?${query.toString()}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
          "X-Sample-Rate": "48000",
          "X-Dtype": "int16",
        },
          // body: await fetchAndDecodeWav("/audio/longer_recording.wav"),
          body: await fetchAndDecodeWav("/audio/longer_recording.wav"),
      }
    );

    const result = await response.json();
    setTranscription(result.transcription || "No transcription");
    setLoading(false);
  };

    return (
        <div style={{ maxWidth: 720, margin: "2rem auto", padding: "1rem" }}>
            <Card>
                <CardContent>
                    <Typography variant="h5" gutterBottom>
                        Audio EQ Settings
                    </Typography>

                    <div style={{ marginBottom: 20 }}>
                        <Typography gutterBottom>Highpass Frequency: {highpass} Hz</Typography>
                        <Slider min={20} max={500} step={10} value={highpass} onChange={(e, v) => setHighpass(v as number)} />
                    </div>

                    <div style={{ marginBottom: 20 }}>
                        <Typography gutterBottom>Lowpass Frequency: {lowpass} Hz</Typography>
                        <Slider min={3000} max={10000} step={100} value={lowpass} onChange={(e, v) => setLowpass(v as number)} />
                    </div>

                    <div style={{ marginBottom: 20 }}>
                        <Typography gutterBottom>Notch 1: {notch1[0]}–{notch1[1]} Hz</Typography>
                        <Slider min={100} max={1000} step={10} value={notch1} onChange={(e, v) => setNotch1(v as number[])} valueLabelDisplay="auto" />
                    </div>

                    <div style={{ marginBottom: 20 }}>
                        <Typography gutterBottom>Notch 2: {notch2[0]}–{notch2[1]} Hz</Typography>
                        <Slider min={100} max={1000} step={10} value={notch2} onChange={(e, v) => setNotch2(v as number[])} valueLabelDisplay="auto" />
                    </div>

                    <div style={{ marginBottom: 20 }}>
                        <Typography gutterBottom>Boost: {boost[0]}–{boost[1]} Hz</Typography>
                        <Slider min={2000} max={6000} step={100} value={boost} onChange={(e, v) => setBoost(v as number[])} valueLabelDisplay="auto" />
                    </div>

                    <Button variant="contained" onClick={sendRequest} disabled={loading} fullWidth>
                        {loading ? "Transcribing..." : "Transcribe with EQ"}
                    </Button>

                    <pre style={{ whiteSpace: "pre-wrap", marginTop: 20 }}>{transcription}</pre>
                </CardContent>
            </Card>
            <Card>
                <CardContent>
                    <AudioVisualizer audioUrl="/audio/longer_recording.wav" />,
                </CardContent>
            </Card>
        </div>
    );
}
