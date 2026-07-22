"""파일 저장/불러오기 모듈 전용 예외."""


class StorageError(Exception):
    """ADOFAI 레벨 파일 저장/불러오기 중 발생하는 오류."""


class AdofaiParseError(StorageError):
    """.adofai 파일(JSON)의 구조가 예상과 달라 파싱할 수 없는 경우."""
