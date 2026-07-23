"""생성된 .adofai 문서가 실제로 플레이 가능한지 검증한다.

여기서 "플레이 가능"은 구체적으로 다음을 의미한다:

1. 구조 검증 — angleData/settings/actions 필수 필드가 있고 타입이 올바르며,
   각도/BPM 값에 NaN이나 무한대가 없다.
2. 타이밍 검증 — 저장된 파일을 실제 게임과 동일한 공식(app/storage/adofai_reader.py)
   으로 다시 읽어, 각 타일 사이 간격이 사람이 반응 가능한 범위인지 확인한다
   (너무 빠르면 사실상 칠 수 없고, 비정상적으로 길면 실수로 정지된 것으로 의심된다).
3. 왕복 일치 검증 — 원본 GeneratedMap과 "저장 후 다시 읽은" 결과의 타일 시각이
   정확히 일치하는지 확인한다. 이게 어긋나면 파일이 열리긴 해도 음악과 싱크가
   깨진 채로 재생된다는 뜻이므로 반드시 오류로 취급한다.

구조/왕복 오류(error)가 있으면 플레이가 불가능하다고 판단한다. 타이밍 경고
(warning)는 플레이는 가능하지만 체감 난이도가 비정상적일 수 있다는 신호다.
"""

import math
from dataclasses import dataclass, field

from app.mapgen.models import GeneratedMap
from app.storage.adofai_reader import parse_adofai_document
from app.storage.exceptions import AdofaiParseError

# 사람이 반응해 탭할 수 있는 현실적인 하한/상한. ADOFAI 최상위 랭커 기준으로도
# 수십 밀리초 단위 타일은 존재하지만, 그보다 짧으면 사실상 판정 자체가
# 불가능한 결함으로 본다. 상한은 "의도한 홀드"가 아니라 버그로 몇 초씩
# 비어버리는 경우를 잡기 위한 값이다.
MIN_TILE_DURATION_SEC = 0.04
MAX_TILE_DURATION_SEC = 15.0
MIN_BPM = 20.0
MAX_BPM = 600.0
ROUND_TRIP_TOLERANCE_SEC = 1e-3


@dataclass
class PlayabilityIssue:
    severity: str  # "error"(플레이 불가) | "warning"(플레이는 가능하나 주의 필요)
    message: str
    tile_index: int | None = None


@dataclass
class PlayabilityReport:
    is_playable: bool
    issues: list[PlayabilityIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[PlayabilityIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[PlayabilityIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def validate_adofai_document(
    document: dict, original_map: GeneratedMap | None = None
) -> PlayabilityReport:
    """.adofai 문서(dict)의 플레이 가능성을 검증한다.

    original_map을 함께 넘기면, 저장 전 맵과 "저장 후 다시 읽은" 결과를
    비교하는 왕복 검증까지 수행한다(export 직후 자체 점검에 사용).
    """
    issues: list[PlayabilityIssue] = _validate_structure(document)
    if any(i.severity == "error" for i in issues):
        return PlayabilityReport(is_playable=False, issues=issues)

    try:
        reconstructed = parse_adofai_document(document)
    except AdofaiParseError as exc:
        issues.append(PlayabilityIssue("error", f"파일을 다시 읽을 수 없습니다: {exc}"))
        return PlayabilityReport(is_playable=False, issues=issues)

    issues.extend(_validate_tile_durations(reconstructed))

    if original_map is not None:
        issues.extend(_validate_round_trip(original_map, reconstructed))

    is_playable = not any(i.severity == "error" for i in issues)
    return PlayabilityReport(is_playable=is_playable, issues=issues)


def _validate_structure(document: dict) -> list[PlayabilityIssue]:
    issues: list[PlayabilityIssue] = []

    angle_data = document.get("angleData")
    if not angle_data or not isinstance(angle_data, list):
        issues.append(PlayabilityIssue("error", "angleData가 비어 있거나 배열이 아닙니다"))
        return issues
    if len(angle_data) < 2:
        issues.append(PlayabilityIssue("error", "타일이 2개 미만이라 플레이할 수 없습니다"))

    for i, angle in enumerate(angle_data):
        if not isinstance(angle, int | float) or isinstance(angle, bool) or not math.isfinite(angle):
            issues.append(
                PlayabilityIssue("error", f"각도 값이 올바르지 않습니다: {angle!r}", tile_index=i)
            )

    settings = document.get("settings")
    if not isinstance(settings, dict):
        issues.append(PlayabilityIssue("error", "settings가 없습니다"))
        return issues

    for key in ("bpm", "songFilename"):
        if key not in settings:
            issues.append(PlayabilityIssue("error", f"settings.{key}가 없습니다"))

    bpm = settings.get("bpm")
    if isinstance(bpm, int | float) and not isinstance(bpm, bool):
        if not math.isfinite(bpm) or bpm <= 0:
            issues.append(PlayabilityIssue("error", f"settings.bpm이 0보다 커야 합니다: {bpm}"))
        elif not (MIN_BPM <= bpm <= MAX_BPM):
            issues.append(
                PlayabilityIssue(
                    "warning", f"BPM({bpm})이 일반적인 범위({MIN_BPM}~{MAX_BPM})를 벗어났습니다"
                )
            )
    elif "bpm" in settings:
        issues.append(PlayabilityIssue("error", "settings.bpm이 숫자가 아닙니다"))

    for action in document.get("actions", []):
        if not isinstance(action, dict):
            issues.append(PlayabilityIssue("error", f"actions 항목이 객체가 아닙니다: {action!r}"))
            continue
        if action.get("eventType") == "SetSpeed":
            value = action.get("beatsPerMinute")
            valid = isinstance(value, int | float) and not isinstance(value, bool) and value > 0
            if not valid:
                issues.append(PlayabilityIssue("error", f"SetSpeed의 BPM이 올바르지 않습니다: {value!r}"))

    return issues


def _validate_tile_durations(reconstructed: GeneratedMap) -> list[PlayabilityIssue]:
    issues: list[PlayabilityIssue] = []
    tiles = reconstructed.tiles

    gaps = [(i, b.time_sec - a.time_sec) for i, (a, b) in enumerate(zip(tiles, tiles[1:]), start=1)]
    too_fast = [i for i, gap in gaps if gap < MIN_TILE_DURATION_SEC]
    too_slow = [i for i, gap in gaps if gap > MAX_TILE_DURATION_SEC]

    if too_fast:
        issues.append(
            PlayabilityIssue(
                "warning",
                f"{len(too_fast)}개 타일 간격이 {MIN_TILE_DURATION_SEC}초보다 짧아 반응하기 어려울 수 있습니다",
            )
        )
    if too_slow:
        issues.append(
            PlayabilityIssue(
                "warning",
                f"{len(too_slow)}개 타일 간격이 {MAX_TILE_DURATION_SEC}초보다 길어 의도치 않은 정지처럼 보일 수 있습니다",
            )
        )

    return issues


def _validate_round_trip(original: GeneratedMap, reconstructed: GeneratedMap) -> list[PlayabilityIssue]:
    issues: list[PlayabilityIssue] = []

    if len(original.tiles) != len(reconstructed.tiles):
        issues.append(
            PlayabilityIssue(
                "error",
                f"타일 개수가 저장 전후 다릅니다: {len(original.tiles)} -> {len(reconstructed.tiles)}",
            )
        )
        return issues

    max_drift = 0.0
    drift_index = -1
    for i, (o, r) in enumerate(zip(original.tiles, reconstructed.tiles)):
        drift = abs(o.time_sec - r.time_sec)
        if drift > max_drift:
            max_drift = drift
            drift_index = i

    if max_drift > ROUND_TRIP_TOLERANCE_SEC:
        issues.append(
            PlayabilityIssue(
                "error",
                f"저장된 파일을 다시 읽으면 원본과 최대 {max_drift:.4f}초 타이밍이 어긋납니다 "
                "(음악 싱크가 깨집니다)",
                tile_index=drift_index,
            )
        )

    return issues
