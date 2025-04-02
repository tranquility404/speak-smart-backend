import base64
import io
import json
import re
import tempfile
from pathlib import Path

from fastapi import UploadFile

async def save_file_temporarily(file: UploadFile):
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
        temp_file.write(await file.read())
        temp_file.flush()
        temp_file_path = temp_file.name
        return temp_file_path

async def save_file(file: UploadFile):
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        buffer.write(await file.read())
        buffer.flush()
        return file_path

def convert_to_img(fig):
    img_io = io.BytesIO()  # Create an in-memory bytes buffer
    fig.savefig(img_io, format='png', bbox_inches='tight')  # Save figure to buffer
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode()
    img_io.flush()
    print("img", img_base64)
    return img_base64

def extract_json_from_llm(data):
    match = re.search(r'\{.*}', data, re.DOTALL)

    if not match:
        print("Data not found in llm output")
        return json.loads("{}")

    json_data = json.loads(match.group())
    return json_data

def save_base64_img(base64_string, file_name):
    audio_bytes = base64.b64decode(base64_string)

    with open(file_name, "wb") as image_file:
        image_file.write(audio_bytes)

def audio_to_base64(file_path):
    with open(file_path, "rb") as audio_file:
        base64_string = base64.b64encode(audio_file.read()).decode("utf-8")
    return base64_string

def read_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()