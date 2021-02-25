from typing import ContextManager
from typing import List
from typing import Optional
from typing import Tuple


class Microphone(ContextManager['Microphone']):
    ...


class AudioData:
    ...


class Recognizer:
    def adjust_for_ambient_noise(self, source: Microphone) -> None: ...

    def listen(self, source: Microphone) -> AudioData: ...

    def recognize_sphinx(self,
                         audio_data: AudioData,
                         language: str='en-US',
                         keyword_entries: Optional[List[Tuple[str, int]]]=None,
                         grammar: Optional[str]=None,
                         show_all: bool=False) -> str: ...
