import asyncio
import time
from datetime import datetime, timezone
import json
import os
import uuid
from dataclasses import asdict
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, Body, WebSocket, WebSocketDisconnect, UploadFile, File, Query, BackgroundTasks, \
    HTTPException
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

task_executor = ThreadPoolExecutor(max_workers=5)  # Adjust number based on your server's capacity

@router.post("/upload-audio/")
async def upload_audio(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    print(file.filename)

    file_path = await save_file(file)
    file_path = str(file_path)
    audio_base64 = audio_to_base64(file_path)

    print("file saved", file_path)
    uid = uuid.uuid4()
    uid = str(uid)

    analyze_speech = AnalyzeSpeech()
    analysis_report = AnalysisReport(audio_base64=audio_base64)

    analysis_requests[uid] = {
        "file_path": file_path,
        "analyze_speech_obj": analyze_speech,
        "report": analysis_report,
        "current_task": None,
        "last_update": asyncio.get_event_loop().time()
    }

    # Start the analysis in a separate thread to not block the event loop
    task_executor.submit(
        run_analysis_in_thread,
        uid,
        file_path,
        analyze_speech,
        analysis_report,
        str(current_user["email"])
    )

    # Cleanup task - keep this async
    asyncio.create_task(remove_file_after_timeout(uid))

    return JSONResponse(content={
        "status": "uploaded successfully",
        "id": uid
    })

def run_analysis_in_thread(uid: str, file_path: str, analyze_speech: AnalyzeSpeech, analysis_report: AnalysisReport, user_email: str):
    """Run the analysis tasks in a separate thread"""
    try:
        tasks = [
            ("load_audio", lambda: load_audio(file_path, analyze_speech)),
            ("transcription", lambda: get_transcription(file_path, analyze_speech, analysis_report)),
            ("speech_rate", lambda: get_speech_rate(analyze_speech, analysis_report)),
            ("intonation", lambda: get_intonation(analyze_speech, analysis_report)),
            ("energy", lambda: get_energy(analyze_speech, analysis_report)),
            ("confidence", lambda: get_confidence(analyze_speech, analysis_report)),
            ("conversation_score", lambda: get_conversation_score(analyze_speech, analysis_report)),
            ("vocal_analysis", lambda: get_vocal_analysis(analyze_speech, analysis_report)),
            ("speech_rate_fig", lambda: get_speech_rate_fig(analyze_speech, analysis_report)),
            ("intonation_fig", lambda: get_intonation_fig(analyze_speech, analysis_report)),
        ]

        for task_name, task_func in tasks:
            # Update the current task with thread-safe updates
            update_analysis_status(uid, task_name)

            # Execute the task
            task_func()

            if uid in analysis_requests:
                analysis_requests[uid]["report"] = analysis_report

            # Small sleep to prevent hogging CPU
            time.sleep(0.1)

        # After all tasks complete, save the report
        id = ObjectId()
        data = convert_report_to_string(analysis_report)
        analysis_report_url = clean_up(str(id), file_path, data)

        # Run the DB save operation in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(save_report_to_db(id, analysis_report_url, analysis_report, user_email))
        loop.close()

        # Mark as complete
        analysis_report.status = "Loaded✅"
        update_analysis_status(uid, None)

    except Exception as e:
        print(f"Error in background analysis for {uid}: {str(e)}")
        analysis_report.status = "Loaded✅"
        if uid in analysis_requests:
            analysis_requests[uid]["report"] = analysis_report


def update_analysis_status(uid: str, task_name=None, error=None):
    """Thread-safe update of the analysis status"""
    try:
        if uid in analysis_requests:
            if task_name is not None:
                analysis_requests[uid]["current_task"] = task_name
            if error is not None:
                analysis_requests[uid]["error"] = error
            # Update timestamp using system time instead of event loop time
            analysis_requests[uid]["last_update"] = time.time()
    except Exception as e:
        print(f"Error updating analysis status: {str(e)}")


@router.get("/analysis-status/{id}")
async def get_analysis_status(id: str, current_user: User = Depends(get_current_user)):
    """Regular HTTP endpoint to check current analysis status"""
    if id not in analysis_requests:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_report = analysis_requests[id]["report"]

    # Get the current state
    try:
        # Add additional status info to the response
        result = json.loads(convert_report_to_string(analysis_report))
        result["current_task"] = analysis_requests[id]["current_task"]

        # Add error info if present
        if "error" in analysis_requests[id]:
            result["error"] = analysis_requests[id]["error"]

        return result
    except Exception as e:
        # Fallback to simpler response if there's an error
        return {
            "current_task": analysis_requests[id]["current_task"],
            "error": str(e)
        }

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
