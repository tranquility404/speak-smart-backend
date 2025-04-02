import librosa
import noisereduce as nr
import numpy as np

from dto.analysis_report import SpeechRateSegment
from model.awkward_pause import AwkwardPause
from model.energy import Energy
from model.intonation import Intonation
from model.speech_rate import SpeechRate
from services.llm_api import transcribe, get_llm_analysis, VocabAnalysis
from utils.utils import extract_json_from_llm

class AnalyzeSpeech:
    def get_transcription(self, file_path):
        self.whisper_result = transcribe(file_path)
        self.transcription = self.whisper_result.text
        return self.transcription

    def load_audio(self, file_path):
        self.y, self.sr = librosa.load(file_path, sr=None)
        self.duration = librosa.get_duration(y=self.y, sr=self.sr)

    def get_vocab_analysis(self):
        data = get_llm_analysis(self.transcription)

        json_data = extract_json_from_llm(data)
        vocab_analysis = VocabAnalysis(json_data)

        print("vocab analysis", str(vocab_analysis))

        self.llm_output = json_data
        self.vocab_analysis = vocab_analysis
        return vocab_analysis

    def get_speech_rate(self):
        timeline = []
        speech_rates = []

        slowest_segment = None
        fastest_segment = None

        for segment in self.whisper_result.segments:
        # for segment in self.whisper_result["segments"]:
            start_time = segment["start"]
            end_time = segment["end"]
            duration = end_time - start_time
            num_words = len(segment['text'].split())
            speech_rate = num_words / duration * 60 if duration > 0 else 0  # words/sec

            if speech_rate == 0:
                continue
            if slowest_segment is None or speech_rate < slowest_segment.speech_rate:
                slowest_segment = SpeechRateSegment(speech_rate=speech_rate, type="slow", start=start_time, end=end_time)

            if fastest_segment is None or speech_rate > fastest_segment.speech_rate:
                fastest_segment = SpeechRateSegment(speech_rate=speech_rate, type="fast", start=start_time, end=end_time)

            timeline.append(end_time)
            speech_rates.append(speech_rate)

        avg_speech_rate = np.mean(speech_rates)
        speech_rate = SpeechRate(avg_speech_rate=avg_speech_rate, slowest_segment=slowest_segment, fastest_segment=fastest_segment, speech_rates=speech_rates, timeline=timeline)
        self.speech_rate = speech_rate
        print("speech rate", vars(speech_rate))

        return speech_rate

    def get_intonation(self):
        y_filtered = librosa.effects.preemphasis(self.y)
        f0, voiced_flag, voiced_probs = librosa.pyin(y=y_filtered, fmin=80, fmax=400)
        valid_pitches = f0[voiced_flag]
        if len(valid_pitches) <= 0:
            self.intonation = None
            return 0

        pitch_values = np.array(valid_pitches)
        times = librosa.times_like(pitch_values, sr=self.sr)

        # Filter out NaN values
        valid_indices = ~np.isnan(pitch_values)
        pitch_values = pitch_values[valid_indices]
        times = times[valid_indices]

        intonation = Intonation(pitch_values=pitch_values, times=times, duration=self.duration)

        self.intonation = intonation
        # print("pitch variation", vars(intonation))
        return intonation

    def get_pauses(self, threshold=0.01, min_pause_duration=0.3):
        rms = librosa.feature.rms(y=self.y)[0]

        # Duration of each frame in seconds
        hop_length = 512
        frame_duration = hop_length / self.sr

        # Identify frames below loudness threshold (potential pauses)
        silent_frames = rms < threshold

        # Count continuous regions of low loudness as distinct pauses
        num_pauses = 0
        pause_duration = 0

        for i in range(len(silent_frames)):
            if silent_frames[i]:
                pause_duration += frame_duration
            else:
                if pause_duration >= min_pause_duration:
                    num_pauses += 1
                pause_duration = 0

        # Catch pause at the end of audio
        if pause_duration >= min_pause_duration:
            num_pauses += 1

        pauses = AwkwardPause(pause_count=num_pauses, duration=self.duration)
        self.pauses = pauses
        print("pauses", vars(pauses))
        return pauses

    def get_energy(self):
        y_reduced = nr.reduce_noise(y=self.y, sr=self.sr, prop_decrease=0.1)
        energy = librosa.feature.rms(y=y_reduced)[0]
        energy = Energy(energy=energy)

        self.energy = energy
        print("energy", vars(energy))
        return energy

    def get_conversation_score(self):
        part = 0.25
        speech_rate_score = (part * self.speech_rate.percent)
        intonation_score = 0
        if self.intonation:
            intonation_score = (part * self.intonation.percent)
        energy_score = (part * self.energy.percent)
        confidence_score = (part * self.pauses.percent)

        conversation_score = speech_rate_score + intonation_score + energy_score + confidence_score
        return conversation_score