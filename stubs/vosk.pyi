from typing import overload

class Model:
    def __init__(self, model_path: str):
        ...

    def vosk_model_find_word(self, word: str) -> int:
        ...


class SpkModel:
    def __init__(self, model_path: str):
        ...


class KaldiRecognizer:
    @overload
    def __init__(self, model: Model, sample_rate: float):
        ...

    @overload
    def __init__(self, model: Model, spk_model: SpkModel, sample_rate: float):
        ...

    @overload
    def __init__(self, model: Model, sample_rate: float, grammar: str):
        ...

    def AcceptWaveform(self, data: bytes) -> int:
        ...

    def Result(self) -> str:
        ...

    def PartialResult(self) -> str:
        ...

    def FinalResult(self) -> str:
        ...
