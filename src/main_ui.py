from alarm_clock import Alarm
from console_ui import ConsoleUI, ScheduleTable, InputLine
from datetime import datetime

from pymongo.collection import Collection

from statuses import StatusCodes


class AppUI:
    """The main UI for the app. This is a table that shows the topics that have been submitted."""

    def __init__(self, submission_topics: Collection, with_manual_input: bool = True):
        self.submission_topics = submission_topics

        # Setup the console UI
        self.submission_table = ScheduleTable()

        # Setup the alarm clock (non-blocking) to update the submission table
        self.update_alarm = Alarm()
        self.update_alarm.set_alarm(0.25, repeating=True)

        # Setup the console UI
        self.console_ui = ConsoleUI([self.submission_table])

        # This is only used for manual theme submission
        if with_manual_input:
            self.theme_prompter = InputLine(
                "* Theme: ",
                escape_callback=lambda: exit(0),
                enter_callback=lambda theme: self.add_topic_submission(
                    theme, "Console"
                ),
            )
            self.console_ui.add_panel(self.theme_prompter)

    def add_topic_submission(self, theme: str, requested_by: str):
        self.submission_topics.insert_one(
            {
                "theme": theme,
                "status": StatusCodes.ADDED,
                "requested_by": requested_by,
                "requested_at": datetime.now().strftime("%H:%M:%S.%f")[0:-3],
            }
        )

    def update(self):
        self.console_ui.update()

        # Update the submission table from the database
        if self.update_alarm.check_alarm():
            self.submission_table.pull_data(
                [
                    (
                        f"...{str(topic['_id'])[-10:]}",
                        topic["theme"],
                        topic["status"],
                        topic["requested_by"],
                        topic["requested_at"],
                    )
                    for topic in self.submission_topics.find()
                ]
            )
