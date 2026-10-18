from datetime import datetime
import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import CallSession
from app.schemas import AgentInfo, SignedUrlResponse, CallEndRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Agent"])

ELEVENLABS_SIGNED_URL_ENDPOINT = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"

@router.get("/info", response_model=AgentInfo)
def get_agent_info():
    """Returns general status and agent_id without exposing sensitive keys."""
    if not settings.agent_id:
        raise HTTPException(status_code=500, detail="AGENT_ID is not configured in .env")
    return AgentInfo(
        agent_id=settings.agent_id,
        phone_number=settings.phone_number,
        status="configured" if settings.elevenlabs_api_key else "missing_api_key",
        environment=settings.environment
    )

@router.get("/signed-url", response_model=SignedUrlResponse)
async def get_signed_url():
    """
    Generates a secure, temporary signed WebSocket URL from ElevenLabs.
    The client web browser uses this signed URL to call the agent without needing your API key.
    """
    if not settings.agent_id:
        raise HTTPException(
            status_code=500,
            detail="AGENT_ID is not set in environment or .env"
        )
    if not settings.elevenlabs_api_key:
        raise HTTPException(
            status_code=500,
            detail="ELEVENLABS_API_KEY is not set in environment or .env"
        )

    headers = {
        "xi-api-key": settings.elevenlabs_api_key
    }
    params = {
        "agent_id": settings.agent_id
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                ELEVENLABS_SIGNED_URL_ENDPOINT,
                headers=headers,
                params=params
            )

        if response.status_code != 200:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ElevenLabs API rejected request: {response.text}"
            )

        data = response.json()
        signed_url = data.get("signed_url")
        if not signed_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve signed_url from ElevenLabs response"
            )

        return SignedUrlResponse(
            signed_url=signed_url,
            agent_id=settings.agent_id
        )

    except httpx.RequestError as exc:
        logger.error(f"Network error contacting ElevenLabs: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Unable to reach ElevenLabs API: {str(exc)}"
        )

@router.post("/session-log")
def log_session(request: CallEndRequest, db: Session = Depends(get_db)):
    """Logs conversation summary and transcripts after a call ends."""
    call = CallSession(
        conversation_id=request.conversation_id,
        status="completed",
        duration_seconds=request.duration_seconds or 0,
        transcript=request.transcript,
        summary=request.summary,
        ended_at=datetime.utcnow()
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return {"status": "success", "session_id": call.id}
