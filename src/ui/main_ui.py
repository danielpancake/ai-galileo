from datetime import datetime
from loguru import logger
from pymongo.collection import Collection

from ui.console_ui import ConsoleUI, ScheduleTable, InputLine
from system.alarm_clock import Alarm
from system.status import StatusCode

import pytchat
import re


class AppUI:
    """The main UI for the app. This is a table that shows the topics that have been submitted."""

    def __init__(
        self,
        submission_topics: Collection,
        with_manual_input: bool = True,
        yt_stream_id: str = None,
    ):
        self.submission_topics = submission_topics
        self.yt_chat = None

        # Setup the console UI
        self.submission_table = ScheduleTable()

        # Setup the alarm clock (non-blocking) to update the submission table
        self.update_alarm = Alarm()
        self.update_alarm.set_alarm(0.25, repeating=True)

        # Setup the console UI
        self.console_ui = ConsoleUI([self.submission_table])

        if with_manual_input or yt_stream_id is None:
            # This is only used for manual theme submission
            self.theme_prompter = InputLine(
                "* Theme: ",
                escape_callback=lambda: exit(0),
                enter_callback=lambda theme: self.add_topic_submission(
                    theme, "Console"
                ),
            )
            self.console_ui.add_panel(self.theme_prompter)
        else:
            self.yt_chat = pytchat.create(yt_stream_id)

    def add_topic_submission(self, theme: str, requested_by: str):
        logger.info(f"New topic submission: {theme}")

        self.submission_topics.insert_one(
            {
                "theme": theme,
                "status": StatusCode.SCHEDULED,
                "requested_by": requested_by,
                "requested_at": datetime.now().strftime("%H:%M:%S.%f")[0:-3],
            }
        )

    def poll_youtube(self):
        """Poll YouTube Stream chat for new topic submissions."""
        if self.yt_chat.is_alive():
            for c in self.yt_chat.get().sync_items():
                if not re.search(r"!topic", c.message):
                    continue

                theme = re.sub(r"!topic", "", c.message).strip()

                # Add to submission topics
                self.add_topic_submission(theme, c.author.name)

    def update(self):
        self.console_ui.update()

        if self.yt_chat is not None:
            self.poll_youtube()

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
