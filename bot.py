import logging
import os
from datetime import timedelta, timezone

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher, JobQueue

import handle
import job

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
TZ = timezone(timedelta(hours=8))


class TelegramBot():
    def __init__(self):
        self.updater: Updater = Updater(
            token=os.getenv("BOT_TOKEN"),
            use_context=True,
        )
        self.dispatcher: Dispatcher = self.updater.dispatcher
        self.job_queue: JobQueue = self.updater.job_queue

        # Filters
        self.TEXT_MSG = Filters.text & (~Filters.command)
        self.UPLOAD = Filters.video | Filters.photo | Filters.document | Filters.animation

        # Attach handlers
        self.dispatcher.add_handler(CommandHandler(handle.ASK, handle.Ask))
        self.dispatcher.add_handler(CommandHandler(handle.LEADERBOARD, handle.Leaderboard, run_async=True))
        self.dispatcher.add_handler(MessageHandler(self.UPLOAD, handle.Submit))
        # self.dispatcher.add_handler(PollHandler(handle.UpdatePoll))
        self.dispatcher.add_handler(MessageHandler(Filters.all, handle.Start, run_async=True))

        # Add schedules
        job.Schedule(self.job_queue)

        # Listen and Serve
        self.updater.start_polling()  # non-blocking
        self.updater.idle()           # blocking


def main():
    TelegramBot()


if __name__ == "__main__":
    main()
