
from fastapi import FastAPI, Request, Header, Query, HTTPException
from fastapi.responses import JSONResponse

from lib.speech.stt import transcribe_pcm, process_and_transcribe_pcm, equalize_and_transcribe_pcm
import asyncio

app = FastAPI()

@app.post("/transcribe_pcm")
async def transcribe_pcm_endpoint(
    request: Request,
    x_sample_rate: int = Header(16000),
    x_dtype: str = Header("int16")
):
    if x_dtype != "int16":
        return JSONResponse({"error": "Only int16 PCM supported for now"}, status_code=400)

    pcm_data = bytearray()
    async for chunk in request.stream():
        pcm_data.extend(chunk)

    # Now call your transcription logic
    transcription = transcribe_pcm(pcm_data, x_sample_rate)
    print("final transcription", transcription)
    return {"transcription": transcription}


app = FastAPI()

def parse_freq_pair(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    try:
        low, high = map(int, value.split('-'))
        return (low, high)
    except Exception:
        return None

@app.post("/transcribe_pcm/equalized")
async def transcribe_pcm_endpoint_equalized(
    request: Request,
    x_sample_rate: int = Header(16000),
    x_dtype: str = Header("int16"),
    highpass: int = Query(90),
    lowpass: int = Query(7500),
    notch1: str = Query("200-300"),
        notch2: str = Query("400-700"),
):
    try:
        # Read raw body bytes
        pcm_data = await request.body()

        eq_args = {
            "highpass": highpass,
            "lowpass": lowpass,
            "notch1": parse_freq_pair(notch1),
            "notch2": parse_freq_pair(notch2),
        }

        if x_dtype != "int16":
            raise HTTPException(status_code=400, detail="Only int16 PCM supported for now")

        print(f"Received PCM data length: {len(pcm_data)}")

        # Assuming equalize_and_transcribe_pcm is imported and synchronous
        transcription = equalize_and_transcribe_pcm(bytearray(pcm_data), x_sample_rate, **eq_args)
        print("final transcription", transcription)
        return JSONResponse(content={"transcription": transcription})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
