import numpy as np
from matplotlib import pyplot as plt

from dto.analysis_report import Param

class Intonation:
    def __init__(self, pitch_values, times, duration):
        self.pitch_values = pitch_values
        self.times = times

        # Calculate statistics
        self.mean_pitch = np.mean(pitch_values)
        # std_pitch = np.std(pitch_values)
        self.min_pitch = np.min(pitch_values)
        self.max_pitch = np.max(pitch_values)

        print("\nPitch Variation Statistics:")
        print(f"Average Pitch: {self.mean_pitch:.1f} Hz")
        # print(f"Standard Deviation: {std_pitch:.1f} Hz")
        print(f"Pitch Range: {self.min_pitch:.1f} Hz - {self.max_pitch:.1f} Hz")

        crossings = np.sum((np.array(pitch_values[:-1]) - self.mean_pitch) * (np.array(pitch_values[1:]) - self.mean_pitch) < 0)
        crossing_rate = crossings / duration

        score = ((self.max_pitch - self.min_pitch) * 0.5) + (crossing_rate * 0.5)
        print("score", score)

        self.category = ("high" if score > 50 else
                         "good" if 25 <= score <= 50 else
                         "low")

        if self.category == "good":
            self.percent = 50 + (score - 25) * 2
        elif self.category == "low":
            self.percent = (score / 25) * 50
        else:  # "high"
            self.percent = 100 - (score - 50)

# if self.category == "good":
        #     self.percent = 70 + (self.pitch_range - 70) * (30 / 30)
        # elif self.category == "slightly monotone":
        #     self.percent = 30 + (self.pitch_range - 50) * (40 / 20)
        # elif self.category == "highly engaging":
        #     self.percent = 70 - (self.pitch_range - 100) * (40 / 50)
        # else:
        #     self.percent = max(0, 30 - abs(self.pitch_range - (50 if self.pitch_range < 50 else 150)) * (30 / 100))

        self.remark = {
            "high": "Tone is too exaggerated — reduce variation for clarity.",
            "good": "Good pitch variation! The speaker uses dynamic pitch changes for engagement.",
            "low": "The speaker shows limited pitch variation. This might sound monotonous.",
        }[self.category]

    def get_graph(self):
        fig, ax = plt.subplots()
        plt.plot(self.times, self.pitch_values, color='b', label='Pitch')

        ax.scatter(
            self.times[np.argmin(self.pitch_values)],
            self.min_pitch,
            color='red', label=f"Lowest: {self.min_pitch:.2f} Hz", s=100, zorder=5
        )

        ax.scatter(
            self.times[np.argmax(self.pitch_values)],
            self.max_pitch,
            color='green', label=f"Highest: {self.max_pitch:.2f} Hz", s=100, zorder=5
        )

        plt.title('Pitch Variation Analysis')
        plt.xlabel('Time (s)')
        plt.ylabel('Pitch (Hz)')
        plt.axhline(self.mean_pitch, color='r', linestyle='--', label=f'Mean Pitch: {self.mean_pitch:.1f} Hz')
        plt.legend()

        self.fig = fig
        return fig

    def get_dto(self):
        return Param(
            avg=self.mean_pitch,
            percent=self.percent,
            category=self.category,
            remark=self.remark
        )
