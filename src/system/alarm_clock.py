import datetime


class Alarm:
    """A simple alarm clock that can be used to schedule events."""

    def __init__(self) -> None:
        self.scheduled_time = None
        self.repeating = False

        self.__delta = None

    def set_alarm(self, in_seconds: int, repeating: bool = False) -> None:
        self.scheduled_time = datetime.datetime.now() + datetime.timedelta(
            seconds=in_seconds
        )
        self.repeating = repeating

        self.__delta = in_seconds

    def check_alarm(self) -> bool:
        if self.scheduled_time is None:
            return False

        if datetime.datetime.now() >= self.scheduled_time:
            if self.repeating:
                self.scheduled_time += datetime.timedelta(seconds=self.__delta)
            else:
                self.scheduled_time = None

            return True

        return False
