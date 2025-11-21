
from dataclasses import dataclass

@dataclass
class TimeRange:
    start: float
    end: float

    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class LessonSegment(TimeRange):
    index: int

