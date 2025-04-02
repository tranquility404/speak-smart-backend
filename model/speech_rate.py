import numpy as np
from matplotlib import pyplot as plt

from dto.analysis_report import SpeechRateSegment, SpeechRateDto

class SpeechRate:
    def __init__(self, avg_speech_rate, slowest_segment: SpeechRateSegment, fastest_segment: SpeechRateSegment, speech_rates, timeline):
        self.avg_speech_rate = avg_speech_rate  # words/min
        self.timeline = timeline
        self.speech_rates = speech_rates

        self.slowest_segment = slowest_segment
        self.fastest_segment = fastest_segment

        self.category = ("very slow" if avg_speech_rate < 100 else
                        "slow" if avg_speech_rate < 130 else
                        "very fast" if avg_speech_rate > 200 else
                        "fast" if avg_speech_rate > 175 else
                        "good")

        if self.category == "good":  # 130 to 175
            self.percent = 50 + (avg_speech_rate - 130) * (20 / 45)  # 50 to 70%
        elif self.category == "slow":  # 100 to 130
            self.percent = 30 + (avg_speech_rate - 100) * (20 / 30)  # 30 to 50%
        elif self.category == "fast":  # 175 to 200
            self.percent = 50 + (avg_speech_rate - 175) * (20 / 25)  # 50 to 70%
        elif self.category == "very slow":  # <100
            self.percent = max(0, 30 - (100 - avg_speech_rate) * (30 / 100))  # 0 to 30%
        else:  # "very fast" (>200)
            self.percent = min(100, 70 + (avg_speech_rate - 200) * (30 / 100))  # 70 to 100%

        self.remark = {
            "very slow": "Increase your pace to make the speech more engaging.",
            "slow": "Speed up slightly to keep the speech more dynamic.",
            "very fast": "Slow down to make the speech clearer and more effective.",
            "fast": "Reduce the speed a bit for better impact.",
            "good": "Well-paced! Keep the flow consistent."
        }[self.category]

    def get_graph(self):
        fig, ax = plt.subplots()

        timeline = np.array(self.timeline)
        speech_rates = np.array(self.speech_rates)
        ax.plot(timeline, speech_rates, label="Speech Rate", color="blue")

        # Highlight mean speech rate
        ax.axhline(y=self.avg_speech_rate, color='orange', linestyle='--', label=f'Mean: {self.avg_speech_rate:.2f} wpm')

        # Highlight slowest segment
        if self.slowest_segment:
            ax.scatter(
                self.slowest_segment.end,
                self.slowest_segment.speech_rate,
                color='red', label=f"Slowest: {self.slowest_segment.speech_rate:.2f} wpm", s=100, zorder=5
            )

        # Highlight fastest segment
        if self.fastest_segment:
            ax.scatter(
                self.fastest_segment.end,
                self.fastest_segment.speech_rate,
                color='green', label=f"Fastest: {self.fastest_segment.speech_rate:.2f} wpm", s=100, zorder=5
            )

        ax.set_title("Speech Rate Analysis")
        ax.set_xlabel("Segment Index")
        ax.set_ylabel("Speech Rate (words/sec)")
        ax.legend()

        return fig

    def get_dto(self):
        return SpeechRateDto(
            avg=self.avg_speech_rate,
            percent=self.percent,
            category=self.category,
            remark=self.remark,
            slowest_segment=self.slowest_segment,
            fastest_segment=self.fastest_segment
        )

