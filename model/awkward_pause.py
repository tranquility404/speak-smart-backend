from dto.analysis_report import Param

class AwkwardPause:
    def __init__(self, pause_count, duration):
        self.pause_count = pause_count
        self.pause_rate = pause_count / duration

        self.category = ("less pauses" if self.pause_rate < 2 else
                         "many pauses" if self.pause_rate > 8 else
                         "excellent")

        if self.category == "less pauses":
            self.percent = 90 - (self.pause_rate * (40 / 2))  # Higher percentage for fewer pauses
        elif self.category == "excellent":
            self.percent = 70 - (self.pause_rate - 2) * (20 / 6)
        else:  # "high" category
            self.percent = 50 - (self.pause_rate - 8) * (30 / 4)

        self.remark = {
            "less pauses": "Minimal pauses convey strong confidence and authority.",
            "excellent": "Well-balanced pauses — projecting confidence and clarity.",
            "many pauses": "Excessive pauses may weaken confidence; aim for a smoother flow."
        }[self.category]

        # self.category = ("very few" if self.pause_rate < 0.05 else
        #                  "few" if self.pause_rate < 0.1 else
        #                  "too many" if self.pause_rate > 0.5 else
        #                  "many" if self.pause_rate > 0.3 else
        #                  "good")
        #
        # if self.category == "good":
        #     self.pause_percent = 70 + (self.pause_rate - 0.05) * (30 / 0.05)
        # elif self.category in ["few", "many"]:
        #     self.pause_percent = 30 + (self.pause_rate - 0.1) * (40 / 0.2)
        # else:
        #     self.pause_percent = max(0, 30 + (self.pause_rate - 0.5) * (-30 / 0.5))
        #
        #
        # self.remark = {
        #     "very few": "Add more pauses to give the speech a natural flow.",
        #     "few": "Try to add slight pauses for better pacing.",
        #     "many": "Reduce pauses slightly to keep the flow smooth.",
        #     "too many": "Limit the number of pauses to avoid breaking the flow.",
        #     "good": "Perfect use of pauses!"
        # }[self.category]

    def get_dto(self):
        return Param(
            avg=self.pause_count,
            percent=self.percent,
            category=self.category,
            remark=self.remark
        )
