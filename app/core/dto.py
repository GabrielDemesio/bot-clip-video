
from dataclasses import dataclass

@dataclass
class TimeRange:
    start: float  # in seconds
    end: float    # in seconds

    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class LessonSegment(TimeRange):
    index: int  # 1-based position within the video

