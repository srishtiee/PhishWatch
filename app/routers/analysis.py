from typing import Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from bson import ObjectId

from app.dependencies.auth import get_current_user
from app.db.mongo import get_db
from app.storage.gridfs import EncryptedGridFS
from app.services.encryption import encrypt_text
from app.services.analysis_client import AnalysisClient
from app.models.entities import Analysis, AnalysisCreate


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/header", response_model=Analysis)
async def submit_header(payload: AnalysisCreate, user: dict = Depends(get_current_user)):
    if not payload.header_text:
        raise HTTPException(status_code=400, detail="header_text is required")
    db = await get_db()
    enc = encrypt_text(payload.header_text)
    doc = Analysis(user_sub=user["sub"], header_enc=enc).model_dump(by_alias=True, exclude_none=True)
    res = await db.analyses.insert_one(doc)

    client = AnalysisClient()
    result = await client.analyze_header(payload.header_text)
    await db.analyses.update_one({"_id": res.inserted_id}, {"$set": {"status": "completed", "result": result}})
    saved = await db.analyses.find_one({"_id": res.inserted_id})
    return Analysis(**saved)


@router.post("/file", response_model=Analysis)
async def upload_eml(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    content = await file.read()
    fs = EncryptedGridFS()
    oid: ObjectId = fs.put(content, filename=file.filename, content_type=file.content_type)

    db = await get_db()
    doc = Analysis(user_sub=user["sub"], eml_file_id=oid).model_dump(by_alias=True, exclude_none=True)
    res = await db.analyses.insert_one(doc)

    client = AnalysisClient()
    result = await client.analyze_file(content)
    await db.analyses.update_one({"_id": res.inserted_id}, {"$set": {"status": "completed", "result": result}})
    saved = await db.analyses.find_one({"_id": res.inserted_id})
    return Analysis(**saved)


@router.get("/", response_model=list[Analysis])
async def list_analyses(user: dict = Depends(get_current_user)):
    db = await get_db()
    docs = db.analyses.find({"user_sub": user["sub"]}).sort("_id", -1)
    return [Analysis(**d) async for d in docs]


@router.get("/{analysis_id}", response_model=Analysis)
async def get_analysis(analysis_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    doc = await db.analyses.find_one({"_id": ObjectId(analysis_id), "user_sub": user["sub"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return Analysis(**doc)

