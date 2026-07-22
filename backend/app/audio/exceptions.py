"""오디오 분석 모듈 전용 예외."""


class AudioAnalysisError(Exception):
    """오디오 분석 중 발생하는 모든 오류의 기반 클래스."""


class UnsupportedAudioFormatError(AudioAnalysisError):
    """지원하지 않는 확장자의 오디오 파일이 입력된 경우."""


class AudioLoadError(AudioAnalysisError):
    """오디오 파일을 찾을 수 없거나 디코딩에 실패한 경우."""
