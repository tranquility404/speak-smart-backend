from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Literal

import numpy as np
from matplotlib.figure import Figure

from services.llm_api import VocabAnalysis
from utils.utils import convert_to_img

T = TypeVar('T')

@dataclass
class Task(Generic[T]):
    status: str = "In Progress..."
    data: Optional[T] = None

@dataclass
class SpeechRateSegment:
    speech_rate: int
    type: Literal["slow", "fast"]
    start: int
    end: int

@dataclass
class Param:
    avg: int
    percent: int
    category: str
    remark: str

@dataclass
class SpeechRateDto(Param):
    slowest_segment: SpeechRateSegment
    fastest_segment: SpeechRateSegment

@dataclass
class AnalysisReport:
    audio: str
    transcription: Task[str]
    speech_rate: Task[SpeechRateDto]
    intonation: Task[Param]
    energy: Task[Param]
    confidence: Task[Param]
    conversation_score: Task[int]

    vocab_analysis: Task[VocabAnalysis]

    speech_rate_fig: Task[str]
    intonation_fig: Task[str]

    # awkward_pause: Task[Param] = Task[Param]()

    def __init__(self, audio_base64):
        self.audio = audio_base64
        self.transcription: Task[str] = Task[str]()
        self.speech_rate: Task[SpeechRateDto] = Task[SpeechRateDto]()
        self.intonation: Task[Param] = Task[Param]()
        self.energy: Task[Param] = Task[Param]()
        self.confidence: Task[int] = Task[int]()
        self.conversation_score: Task[int] = Task[int]()

        self.vocab_analysis: Task[VocabAnalysis] = Task[VocabAnalysis]()

        self.speech_rate_fig: Task[str] = Task[str]()
        self.intonation_fig: Task[str] = Task[str]()

def custom_serializer(o):
    if isinstance(o, np.ndarray):
        return o.tolist()  # Convert numpy arrays to lists
    elif isinstance(o, np.float32):
        return float(o)  # Convert np.float32 to float
    elif isinstance(o, set):
        return list(o)  # Convert sets to lists
    elif isinstance(o, Figure):
        return str(convert_to_img(o))  # Convert Matplotlib figures to a string
    elif hasattr(o, '__dict__'):
        return str(o)  # Convert objects to strings
    return o

if __name__ == "__main__":
    a: Task[Param] = Task()
    print(str(AnalysisReport("")).replace(",", ",\n").replace("(", "(\n-"))