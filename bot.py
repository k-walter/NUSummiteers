import os
import job
import handler
import logging
from datetime import time
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, ConversationHandler, CallbackQueryHandler

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Bot():
    def __init__(self):
        self.updater = Updater(token=os.getenv("BOT_TOKEN"), use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.job_queue = self.updater.job_queue

        # Attach handlers
        self.dispatcher.add_handler(self.ConversationHandler())

        # Add schedules
        # self.job_queue.run_repeating(job.Fact, 10)
        self.job_queue.run_daily(job.Fact, time(12,0,0))
        self.job_queue.run_daily(job.Fact, time(19,0,0))
        self.job_queue.run_daily(job.Progress, time(5,0,0))
        self.job_queue.run_daily(job.Leaderboard, time(5,0,30))
        self.job_queue.run_daily(job.FAQ, time(22,0,0))

        # Listen and Serve
        self.updater.start_polling()    # non-blocking
        self.updater.idle()             # blocking

    def ConversationHandler(self):
        self.isTextMsg = Filters.text & (~Filters.command)
        self.isUpload = Filters.video | Filters.photo | Filters.document | Filters.animation
        return ConversationHandler(
            entry_points=[CommandHandler('start', handler.Start)],
            states={
                handler.START: [
                    CallbackQueryHandler(handler.Submit, pattern=f"^{handler.SUBMIT}$"),
                    CallbackQueryHandler(handler.Ask, pattern=f"^{handler.ASK}$"),
                    CallbackQueryHandler(handler.Progress, pattern=f"^{handler.PROGRESS}$"),
                    CallbackQueryHandler(handler.End, pattern=f"^{handler.END}$"),
                ],
                handler.SUBMIT: [
                    MessageHandler(self.isUpload, handler.Submitted),
                    CallbackQueryHandler(handler.Start, pattern=f"^{handler.START}$"),
                    CallbackQueryHandler(handler.End, pattern=f"^{handler.END}$"),
                ],
                handler.ASK: [
                    MessageHandler(self.isTextMsg, handler.Asked),
                    CallbackQueryHandler(handler.Start, pattern=f"^{handler.START}$"),
                    CallbackQueryHandler(handler.End, pattern=f"^{handler.END}$"),
                ],
                handler.PROGRESS: [
                    CallbackQueryHandler(handler.Start, pattern=f"^{handler.START}$"),
                ],
            },
            fallbacks=[CommandHandler('start', handler.Start)]
        )

def main():
    bot = Bot()

if __name__ == "__main__":
    main()
