"""자연어 지시 기반 맵 구간 편집 API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.edit_engine import apply_edit_instruction
from app.ai.instruction_parser import parse_edit_instruction
from app.ai.models import EditInstruction
from app.mapgen.models import GeneratedMap

router = APIRouter(prefix="/ai", tags=["ai"])


class EditSegmentRequest(BaseModel):
    existing_map: GeneratedMap
    instruction: str
    seed: int | None = None


class EditSegmentResponse(BaseModel):
    map: GeneratedMap
    parsed_instruction: EditInstruction


@router.post("/edit-segment", response_model=EditSegmentResponse)
async def edit_segment(request: EditSegmentRequest) -> EditSegmentResponse:
    drop_times = sorted({tile.time_sec for tile in request.existing_map.tiles if tile.is_drop_emphasis})

    parsed = parse_edit_instruction(
        request.instruction, request.existing_map.duration_sec, drop_times_sec=drop_times
    )

    try:
        new_map = apply_edit_instruction(request.existing_map, parsed, seed=request.seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return EditSegmentResponse(map=new_map, parsed_instruction=parsed)
