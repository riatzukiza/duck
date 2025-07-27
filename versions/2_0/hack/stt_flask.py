
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from lib.speech.stt import transcribe_pcm, process_and_transcribe_pcm, equalize_and_transcribe_pcm
from asgiref.wsgi import WsgiToAsgi


app = Flask(__name__)
CORS(app)  

def transcribe(waveform, sample_rate, chunk_size):
    # Dummy implementation for testing
    return "This is a fake transcription."

@app.route('/transcribe_pcm', methods=['POST'])
def transcribe_pcm_endpoint():
    try:
        pcm_data = request.data
        sample_rate = int(request.headers.get('X-Sample-Rate', 16000))
        dtype = request.headers.get('X-Dtype', 'int16')

        if dtype != 'int16':
            return jsonify({'error': 'Only int16 PCM supported for now'}), 400

        transcription = transcribe_pcm(bytearray(pcm_data), sample_rate)
        print("final transcription",transcription)
        return jsonify({'transcription': transcription})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe_pcm/full_process', methods=['POST'])
def transcribe_pcm_endpoint_full_process():
    try:
        pcm_data = request.data
        sample_rate = int(request.headers.get('X-Sample-Rate', 16000))
        dtype = request.headers.get('X-Dtype', 'int16')

        if dtype != 'int16':
            return jsonify({'error': 'Only int16 PCM supported for now'}), 400

        transcription = process_and_transcribe_pcm(bytearray(pcm_data), sample_rate)
        print("final transcription",transcription)
        return jsonify({'transcription': transcription})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from flask import request

def parse_filter_args():
    def parse_freq_pair(value):
        try:
            low, high = map(int, value.split('-'))
            return (low, high)
        except:
            return None

    return {
        "highpass": int(request.args.get("highpass", 90)),
        "lowpass": int(request.args.get("lowpass", 6200)),
        "notch1": parse_freq_pair(request.args.get("notch1", "200-300")),
        "notch2": parse_freq_pair(request.args.get("notch2", "320-460")),
    }
@app.route('/transcribe_pcm/equalized', methods=['POST'])
def transcribe_pcm_endpoint_equalized():
    try:
        pcm_data = request.data
        sample_rate = int(request.headers.get('X-Sample-Rate', 16000))
        dtype = request.headers.get('X-Dtype', 'int16')

        eq_args = parse_filter_args()

        if dtype != 'int16':
            return jsonify({'error': 'Only int16 PCM supported for now'}), 400

        print(len(pcm_data))

        transcription = equalize_and_transcribe_pcm(bytearray(pcm_data), sample_rate, **eq_args)
        print("final transcription",transcription)
        return jsonify({'transcription': transcription})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
import io
import tempfile
import subprocess
import numpy as np

asgi_app = WsgiToAsgi(app)
if __name__ == '__main__':
    app.run(port=5000)
