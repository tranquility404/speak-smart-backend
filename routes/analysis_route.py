import asyncio
from datetime import datetime, timezone
import json
import os
import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, Body, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from pydantic import BaseModel
from starlette.responses import JSONResponse
from bson import ObjectId

from config.database import analysis_data_collection
from config.gcloud import clean_up
from dto.analysis_report import custom_serializer
from model.user import User
from security.auth import get_current_user, get_current_user_websocket
from services.llm_api import generate_slow_fast_drill, generate_speech, generate_rephrasals, generate_random_topics
from services.task_handler import *
from utils.utils import extract_json_from_llm, save_file, audio_to_base64

router = APIRouter()

analysis_requests = {
    "test-id-123": {
        "file_path": "./uploads/aman.wav",
        "analyze_speech_obj": AnalyzeSpeech(),
        "report": AnalysisReport(audio_base64="")
    }
}

async def save_report_to_db(id: ObjectId, analysis_report_url: str, analysis_report: AnalysisReport, user_email: str):
    analysis_data = {
        "_id": id,
        "requested_by": user_email,
        "request_made_at": datetime.now(timezone.utc),
        "analysis_report_url": analysis_report_url,

        "transcript": " ".join(analysis_report.transcription.data.split()[:5]),
        "speech_rate": convert_report_to_string({
            "avg": analysis_report.speech_rate.data.avg,
            "percent": analysis_report.speech_rate.data.percent,
            "category": analysis_report.speech_rate.data.category
        }),
        "intonation": convert_report_to_string({
            "avg": analysis_report.intonation.data.avg,
            "percent": analysis_report.intonation.data.percent,
            "category": analysis_report.intonation.data.category
        }),
        "energy": convert_report_to_string({
            "avg": analysis_report.energy.data.avg,
            "percent": analysis_report.energy.data.percent,
            "category": analysis_report.energy.data.category
        }),
        "confidence": convert_report_to_string({
            "avg": analysis_report.confidence.data.avg,
            "percent": analysis_report.confidence.data.percent,
            "category": analysis_report.confidence.data.category
        }),
        "conversation_score": analysis_report.conversation_score.data
    }

    result = await analysis_data_collection.insert_one(analysis_data)
    print("Report saved successfully", "id", str(result.inserted_id))

async def remove_file_after_timeout(uid: str, timeout: int = 600):  # clear files after 10 mins
    await asyncio.sleep(timeout)
    if uid in analysis_requests:
        file_path = analysis_requests[uid]["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} deleted from storage after {timeout} seconds.")
        del analysis_requests[uid]

def convert_report_to_string(analysis_report: AnalysisReport|dict):
    if isinstance(analysis_report, AnalysisReport):
        data = json.dumps(asdict(analysis_report), indent=4, default=custom_serializer)
    else:
        data = json.dumps(analysis_report, indent=4, default=custom_serializer)
    return data

@router.websocket("/analysis-report/{id}")
async def websocket_endpoint(websocket: WebSocket, id: str, token: str = Query(None)):
    current_user = await get_current_user_websocket(token)
    if not token or not current_user:
        await websocket.close(code=1008)  # 1008: Policy Violation
        return

    print(id)
    if not id in analysis_requests:
        return

    await websocket.accept()
    file_path: str = analysis_requests[id]["file_path"]
    analysis_report: AnalysisReport = analysis_requests[id]["report"]

    try:
        analyze_speech: AnalyzeSpeech = analysis_requests[id]["analyze_speech_obj"]
        data = convert_report_to_string(analysis_report)
        await websocket.send_text(data)

        if json.loads(data)["intonation_fig"]["status"] == "Loaded✅":
            print("audio already analysed")
            return

        tasks = [
            lambda: load_audio(file_path, analyze_speech),
            lambda: get_transcription(file_path, analyze_speech, analysis_report),
            lambda: get_speech_rate(analyze_speech, analysis_report),
            lambda: get_intonation(analyze_speech, analysis_report),
            lambda: get_energy(analyze_speech, analysis_report),
            lambda: get_confidence(analyze_speech, analysis_report),
            lambda: get_conversation_score(analyze_speech, analysis_report),
            lambda: get_vocal_analysis(analyze_speech, analysis_report),
            lambda: get_speech_rate_fig(analyze_speech, analysis_report),
            lambda: get_intonation_fig(analyze_speech, analysis_report),
        ]

        for completed_task in tasks:
            completed_task()
            await websocket.send_text(convert_report_to_string(analysis_report))

        # Saving Report
        id = ObjectId()
        data = convert_report_to_string(analysis_report)
        analysis_report_url = clean_up(str(id), file_path, data)
        await save_report_to_db(id, analysis_report_url, analysis_report, str(current_user["email"]))

        analysis_report.status = "Loaded✅"
        await websocket.send_text(convert_report_to_string(analysis_report))

    except WebSocketDisconnect as e:
        print("websocket closed", e.reason)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File deleted due to error or disconnection or analysis completion.")


@router.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    print(file.filename)

    file_path = await save_file(file)
    file_path = str(file_path)
    audio_base64 = audio_to_base64(file_path)

    print(file_path)
    uid = uuid.uuid4()
    uid = str(uid)

    analysis_requests[uid] = {
        "file_path": file_path,
        "analyze_speech_obj": AnalyzeSpeech(),
        "report": AnalysisReport(audio_base64=audio_base64)
    }

    asyncio.create_task(remove_file_after_timeout(uid))
    print("file saved: ", file_path)
    # os.unlink(file_path)

    return JSONResponse(content={"status": "uploaded successfully", "id": uid})


@router.post("/generate-random-topics")
async def random_topics(current_user: User = Depends(get_current_user)):
    topics = extract_json_from_llm(generate_random_topics())
    return topics

class TopicRequest(BaseModel):
    topic: str

@router.post("/generate-speech")
async def speech(data: TopicRequest, current_user: User = Depends(get_current_user)):
    return extract_json_from_llm(generate_speech(data.topic))

@router.post("/generate-rephrasals")
async def rephrasals(speech: str = Body(...), current_user: User = Depends(get_current_user)):
    rephrasals_data = extract_json_from_llm(generate_rephrasals(speech))
    return rephrasals_data

@router.post("/generate-slow-fast-drill")
async def slow_fast_drill(current_user: User = Depends(get_current_user)):
    drill = extract_json_from_llm(generate_slow_fast_drill())
    return drill

# @router.get("/generate-mock-interview")
# async def mock_interview():
#     interview_ques = extract_json_from_llm(generate_mock_interview())["mock_interview"]
#
#     for i in interview_ques:
#     return interview_ques
