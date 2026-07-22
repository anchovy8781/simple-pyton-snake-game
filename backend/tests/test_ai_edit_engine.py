from app.ai.edit_engine import apply_edit_instruction
from app.ai.models import EditInstruction
from app.mapgen.engine import generate_map
from app.mapgen.models import Difficulty
from tests.mapgen_fixtures import make_analysis_result


def test_apply_edit_instruction_changes_difficulty_and_only_segment_angles() -> None:
    analysis = make_analysis_result(duration_sec=16.0)
    original_map = generate_map(analysis, Difficulty.NORMAL, seed=1)

    instruction = EditInstruction(
        start_sec=4.0, end_sec=8.0, difficulty_delta=1, raw_instruction="20~35초를 더 어렵게"
    )
    edited_map = apply_edit_instruction(original_map, instruction, seed=2)

    assert edited_map.difficulty == Difficulty.HARD
    assert [t.time_sec for t in edited_map.tiles] == [t.time_sec for t in original_map.tiles]

    for original_tile, new_tile in zip(original_map.tiles, edited_map.tiles):
        if original_tile.time_sec < 4.0 or original_tile.time_sec > 8.0:
            assert original_tile.turn_angle_deg == new_tile.turn_angle_deg


def test_apply_edit_instruction_clamps_difficulty_at_extreme() -> None:
    analysis = make_analysis_result(duration_sec=16.0)
    original_map = generate_map(analysis, Difficulty.EXTREME, seed=1)

    instruction = EditInstruction(start_sec=0.0, end_sec=16.0, difficulty_delta=5, raw_instruction="더 어렵게")
    edited_map = apply_edit_instruction(original_map, instruction, seed=2)

    assert edited_map.difficulty == Difficulty.EXTREME


def test_apply_edit_instruction_clamps_difficulty_at_easy() -> None:
    analysis = make_analysis_result(duration_sec=16.0)
    original_map = generate_map(analysis, Difficulty.EASY, seed=1)

    instruction = EditInstruction(start_sec=0.0, end_sec=16.0, difficulty_delta=-5, raw_instruction="더 쉽게")
    edited_map = apply_edit_instruction(original_map, instruction, seed=2)

    assert edited_map.difficulty == Difficulty.EASY


def test_apply_edit_instruction_flashy_and_reduce_repetition_run_without_error() -> None:
    analysis = make_analysis_result(duration_sec=16.0)
    original_map = generate_map(analysis, Difficulty.NORMAL, seed=1)

    instruction = EditInstruction(
        start_sec=0.0,
        end_sec=16.0,
        emphasize_flashy=True,
        reduce_repetition=True,
        tighten_timing=True,
        raw_instruction="화려하게, 반복 줄이고, 박자 정확하게",
    )
    edited_map = apply_edit_instruction(original_map, instruction, seed=3)

    assert [t.time_sec for t in edited_map.tiles] == [t.time_sec for t in original_map.tiles]
