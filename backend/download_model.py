import requests

url = "https://huggingface.co/onnx-community/emotion-recognition/resolve/main/emotion-recognition-7.onnx?download=1"
outfile = "emotion-recognition-7.onnx"

print("Downloading model (this may take 20-60 seconds)...")

with requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"}) as r:
    r.raise_for_status()
    with open(outfile, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

print("✅ Model downloaded successfully and saved as:", outfile)
