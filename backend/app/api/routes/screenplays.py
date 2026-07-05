import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import select, func
from google import genai

from app.api.deps import CurrentUser, SessionDep
from app.models import Screenplay, ScreenplayPublic, ScreenplaysPublic, Message
from app.core.config import settings

router = APIRouter(prefix="/screenplays", tags=["screenplays"])


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from an uploaded screenplay file (PDF or .txt)."""
    if filename.lower().endswith(".pdf"):
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    else:
        return file_bytes.decode("utf-8", errors="ignore")


def generate_coverage_report(script_text: str) -> dict:
    """Send screenplay text to Gemini and get back a structured coverage report."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = f"""You are a professional script reader for a film studio. Analyze the following screenplay and produce a coverage report.

Return ONLY valid JSON (no markdown, no code fences) with this exact structure:
{{
  "logline": "one sentence summary",
  "genre": "primary genre",
  "tone": "overall tone description",
  "marketability_score": "score out of 10 with brief reasoning",
  "pacing_notes": "brief notes on pacing/structure",
  "character_arcs": "brief summary of main character arcs",
  "comparable_films": ["film1", "film2"],
  "strengths": ["point1", "point2"],
  "weaknesses": ["point1", "point2"]
}}

Screenplay text:
{script_text[:30000]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    import json
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "", 1).strip()
    return json.loads(raw)


@router.get("/", response_model=ScreenplaysPublic)
def read_screenplays(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    count_statement = select(func.count()).select_from(Screenplay).where(Screenplay.owner_id == current_user.id)
    count = session.exec(count_statement).one()
    statement = select(Screenplay).where(Screenplay.owner_id == current_user.id).offset(skip).limit(limit)
    screenplays = session.exec(statement).all()
    return ScreenplaysPublic(data=screenplays, count=count)


@router.get("/{id}", response_model=ScreenplayPublic)
def read_screenplay(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    screenplay = session.get(Screenplay, id)
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay not found")
    if screenplay.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return screenplay


@router.post("/upload", response_model=ScreenplayPublic)
async def upload_screenplay(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    file_bytes = await file.read()
    script_text = extract_text_from_file(file_bytes, file.filename)

    screenplay = Screenplay(
        title=file.filename.rsplit(".", 1)[0],
        filename=file.filename,
        status="processing",
        extracted_text=script_text,
        owner_id=current_user.id,
    )
    session.add(screenplay)
    session.commit()
    session.refresh(screenplay)

    try:
        report = generate_coverage_report(script_text)
        screenplay.coverage_report = report
        screenplay.status = "completed"
    except Exception as e:
        screenplay.status = "failed"
        screenplay.coverage_report = {"error": str(e)}

    session.add(screenplay)
    session.commit()
    session.refresh(screenplay)
    return screenplay


@router.delete("/{id}")
def delete_screenplay(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Message:
    screenplay = session.get(Screenplay, id)
    if not screenplay:
        raise HTTPException(status_code=404, detail="Screenplay not found")
    if screenplay.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(screenplay)
    session.commit()
    return Message(message="Screenplay deleted successfully")