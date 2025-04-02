import numpy as np

from dto.analysis_report import Param

class Energy:
    def __init__(self, energy):
        self.avg_energy = np.mean(energy)
        self.energy_variation = np.std(energy)

        self.category = ("low" if self.avg_energy < 0.04 else
                         "high" if self.avg_energy > 0.08 else
                         "good")

        if self.category == "good":
            self.percent = 70 + (self.avg_energy - 0.04) * (30 / 0.04)
        elif self.category == "low":
            self.percent = 30 + (self.avg_energy - 0.02) * (40 / 0.02)
        else:
            self.percent = max(0, 70 - (self.avg_energy - 0.08) * (40 / 0.02))

        self.remark = {
            "low": "Increase your volume to project more confidence.",
            "good": "Good energy level — sounds confident and clear.",
            "high": "Lower your volume slightly to avoid sounding harsh."
        }[self.category]

        # self.category = ("very low" if self.avg_energy < 0.05 else
        #     "too high" if self.avg_energy > 0.15 else
        #     "good")
        #
        # if self.category == "good":  # 0.05 to 0.15 → 60% to 100%
        #     self.energy_percent = 60 + (self.avg_energy - 0.05) * (40 / 0.1)  # 60 to 100%
        # elif self.category == "very low":  # < 0.05 → 0% to 60%
        #     self.energy_percent = max(0, self.avg_energy / 0.05 * 60)  # 0 to 60%
        # else:  # > 0.15 → 60% to 0%
        #     self.energy_percent = max(0, 100 - ((self.avg_energy - 0.15) / 0.05 * 60))  # 60 to 0%
        #
        # self.remark = {
        #     "very low": "Increase your energy to make the speech more lively.",
        #     "good": "Great energy! Keep it balanced.",
        #     "too high": "Reduce your intensity to maintain a comfortable flow."
        #     }[self.category]

        # self.energy_percent = (100 - (0.05 - self.avg_energy) * 200 if self.avg_energy < 0.05 else
        #                           100 - (0.15 - self.avg_energy) * 100 if self.avg_energy < 0.15 else
        #                           100 - (self.avg_energy - 0.3) * 200 if self.avg_energy > 0.3 else
        #                           100 - (self.avg_energy - 0.15) * 100 if self.avg_energy > 0.15 else
        #                           100)
        #
        # self.category = ("very low" if self.avg_energy < 0.05 else
        #                  "low" if self.avg_energy < 0.1 else
        #                  "too high" if self.avg_energy > 0.3 else
        #                  "high" if self.avg_energy > 0.15 else
        #                  "good")
        #
        # self.remark = {
        #     "very low": "Increase your energy to make the speech more lively.",
        #     "low": "Try to add more vocal strength to sound more engaging.",
        #     "good": "Great energy! Keep it balanced.",
        #     "high": "Control your energy slightly to avoid sounding aggressive.",
        #     "too high": "Reduce your intensity to maintain a comfortable flow."
        # }[self.category]

    def get_dto(self):
        return Param(
            avg=self.avg_energy,
            percent=self.percent,
            category=self.category,
            remark=self.remark
        )
