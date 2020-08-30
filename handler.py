import os
import requests
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import run_async
from datetime import timezone, timedelta, datetime
import logging

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
tz = timezone(timedelta(hours=8))

"""
Conventions:
	PascalCase for exported functions
	camelCase for local functions
	UPPER_CASE for states

	don't stutter, eg exported functions will be handler.StartHandler
	don't print(), use logging.info()
"""

# States
START, END, SUBMIT, SUBMITTED, ASK, ASKED, PROGRESS, LEADERBOARD = map(str,range(8))

goBackMarkup = InlineKeyboardMarkup([
	[InlineKeyboardButton("⬅ Back to Start", callback_data=START)],
	[InlineKeyboardButton("❌ End", callback_data=END)],
])

def Start(update, context):
	isNewConvo = update.message is not None
	if isNewConvo:
		logger.info("User %s started a conversation.", update.message.from_user.first_name)

	"""
	InlineKeyboard displays buttons with text and returns with a string as callback_data
	The keyboard is formatted as a list of lists, like so
	[
		[Row 1 Col 1, Row 1 Col 2],
		[Row 2 Col 1, Row 2 Col 2],
		[Row 3 Col 1, Row 3 Col 2],
	]
	"""
	reply_markup = InlineKeyboardMarkup([
		[InlineKeyboardButton("🎥 Submit Proof", callback_data=SUBMIT)],
		[InlineKeyboardButton("🤔 Ask a Question", callback_data=ASK)],
		[InlineKeyboardButton("❌ End", callback_data=END)],
		])

	# Send message with text and appended InlineKeyboard
	if isNewConvo:
		update.message.reply_text(
			"How can I help you today?",
			reply_markup=reply_markup
			)
	else:
		query = update.callback_query
		query.answer()
		query.edit_message_text(
			"How can I help you today?",
			reply_markup=reply_markup
		)

	# Tell ConversationHandler our current state
	return START

def End(update, context):
	query = update.callback_query
	query.answer()
	query.edit_message_text("🧗 Climb on!")
	return ConversationHandler.END

def Submit(update, context):
	logger.info("I'm in Submit()")
	query = update.callback_query
	query.answer()
	msg = "Upload your activity proof!\n\n🖼 Photos/Screenshots - must reflect elevation gained, timestamp and identification/user ID (if applicable).\n🎬 Videos - must overlay timestamp / begin with video of time (on a phone/watch) and record complete climb from bottom to top\n\nCheck our T&C (in the description) for more info."
	query.edit_message_text(msg, parse_mode='Markdown', reply_markup=goBackMarkup)
	return SUBMIT

@run_async
def Submitted(update, context):
	logger.info("I'm in Submitted()")
	context.bot.send_message(chat_id=update.effective_chat.id, text="Submission Received!")
	msg = f"Name: *{update.message.from_user.first_name}* `t.me/{update.message.from_user.username}`\nTime: {datetime.now(tz)}"
	context.bot.send_message(chat_id=os.getenv("CHANNEL_ID"), text=msg, parse_mode="Markdown")
	context.bot.forward_message(chat_id=os.getenv("CHANNEL_ID"), from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
	return Start(update, context)

def Ask(update, context):
	query = update.callback_query
	query.answer()
	query.edit_message_text("Ask your question below...", reply_markup=goBackMarkup)
	return ASK

@run_async
def Asked(update, context):
	postJSONToSlack({
		"type": "mrkdwn",
		"text": f"Name: *{update.message.from_user.first_name}* `t.me/{update.message.from_user.username}`\n{update.message.text}",
	})
	context.bot.send_message(chat_id=update.effective_chat.id, text="We'll get back to you soon!")
	return Start(update, context)
@run_async
def postJSONToSlack(json):
	requests.post(os.getenv("SLACK_TOKEN"), json=json)

def Unknown(update, context):
	context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

### UNUSED FUNCTIONS (for reference) ###

# scope = ["https://www.googleapis.com/auth/drive"]
# creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
# service = build('drive', 'v3', credentials=creds)
@run_async
def uploadFiletoDrive(name, fileID):
	f = Bot.getFile(fileID)
	logger.info(r)
	r = requests.get(os.getenv("DRIVE_TOKEN"), params={
		'name': name,
		'url': f"https://api.telegram.org/file/bot{os.getenv('BOT_TOKEN')}/{r['file_path']}",
	})
	logger.info(r.text)

def Progress(update, context):
	query = update.callback_query
	query.answer()
	query.edit_message_text(checkProgress())
	return PROGRESS

def Leaderboard(update, context):
	query = update.callback_query
	query.answer()
	query.edit_message_text("You are the 1st ascender!", reply_markup=None)
	return LEADERBOARD

def checkProgress(userID):
	return """Congratulations! You have surpassed 164m.\n\nThat’s the highest point in Singapore!"""

def echo(update, context):
	context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def inline_caps(update, context):
	query = update.inline_query.query
	if not query:
		return

	results = [InlineQueryResultArticle(
		id=query.upper(),
		title='Caps',
		input_message_content=InputTextMessageContent(query.upper())
	)]
	context.bot.answer_inline_query(update.inline_query.id, results)
