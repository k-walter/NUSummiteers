import os
import pytz
import job
import handler
import logging
from datetime import time, timedelta, timezone
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, ConversationHandler, CallbackQueryHandler

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
TZ = timezone(timedelta(hours=8))

class TelegramBot():
	def __init__(self):
		self.updater = Updater(token=os.getenv("BOT_TOKEN"), use_context=True)
		self.dispatcher = self.updater.dispatcher
		self.job_queue = self.updater.job_queue

		# Filters
		self.isTextMsg = Filters.text & (~Filters.command)
		self.isUpload = Filters.video | Filters.photo | Filters.document | Filters.animation

		# Attach handlers
		self.dispatcher.add_handler(self.ConversationHandler())
		self.dispatcher.add_handler(MessageHandler(Filters.all, handler.Unknown))

		# Add schedules
		job.Schedule(self.job_queue)

		# Listen and Serve
		self.updater.start_polling()    # non-blocking
		self.updater.idle()             # blocking

	def ConversationHandler(self):
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
			fallbacks=[
				MessageHandler(self.isTextMsg, handler.Ask),	# stays in state
				MessageHandler(self.isUpload, handler.Reject),	# returns to start
				CommandHandler('start', handler.Start),
			],
			allow_reentry=True,
		)

def main():
	bot = TelegramBot()

if __name__ == "__main__":
	main()
