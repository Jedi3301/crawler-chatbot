import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.bots import BotCreate, BotUpdate, BotResponse
from app.services import db_service
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["Bots"])

@router.post(
    "",
    response_model=BotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Bot",
)
def create_bot(body: BotCreate) -> BotResponse:
    """Creates a new Bot entity which acts as a distinct Pinecone namespace."""
    try:
        record = db_service.create_bot(name=body.name, description=body.description)
        return BotResponse(**record)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

@router.get(
    "",
    response_model=list[BotResponse],
    summary="List all bots",
)
def list_bots() -> list[BotResponse]:
    """Returns all created bots."""
    try:
        records = db_service.list_bots()
        return [BotResponse(**r) for r in records]
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

@router.get(
    "/{bot_id}",
    response_model=BotResponse,
    summary="Get a specific bot",
)
def get_bot(bot_id: str) -> BotResponse:
    """Returns a specific bot."""
    try:
        record = db_service.get_bot(bot_id)
        return BotResponse(**record)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

@router.patch(
    "/{bot_id}",
    response_model=BotResponse,
    summary="Update a specific bot",
)
def update_bot(bot_id: str, body: BotUpdate) -> BotResponse:
    """Updates a bot's details."""
    try:
        record = db_service.update_bot(
            bot_id=bot_id, 
            name=body.name, 
            description=body.description
        )
        return BotResponse(**record)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

@router.get(
    "/{bot_id}/knowledge",
    summary="List knowledge sources for a bot",
)
def get_bot_knowledge(bot_id: str) -> list[dict]:
    """Returns all websites ingested for a specific bot."""
    try:
        return db_service.list_bot_knowledge(bot_id)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
