import json

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from config.database import analysis_data_collection
from config.gcloud import read_gcs_file_as_string
from model.user import User
from security.auth import get_current_user

router = APIRouter()

def document_to_json(doc):
    doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
    doc["analysis_report_url"] = None
    return doc

@router.get("/recent-analysis", response_model=List[dict])
async def recent_analysis(current_user: User = Depends(get_current_user)):
    entries = await analysis_data_collection.find().sort("_id", -1).limit(10).to_list(length=10)
    return [document_to_json(entry) for entry in entries]

@router.get("/get-analysis/{item_id}")
async def get_analysis(item_id: str):
    document = await analysis_data_collection.find_one({"_id": ObjectId(item_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Item not found")

    analysis_report_url = document.get("analysis_report_url")
    if not analysis_report_url:
        raise HTTPException(status_code=400, detail="Analysis report URL not found")

    try:
        file_content = read_gcs_file_as_string(analysis_report_url)
        return json.loads(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))