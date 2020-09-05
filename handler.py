import os
import requests
import gspread
from functools import wraps
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import run_async
from datetime import timezone, timedelta, datetime
import logging

# initialisation
logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
tz = timezone(timedelta(hours=8))
dtFormat = "%a %d/%m/%Y %H:%M:%S"
gc = gspread.service_account(filename='client_secret.json')

# States
START, END, SUBMIT, SUBMITTED, ASK, ASKED, PROGRESS, LEADERBOARD = map(str,range(8))

# Global variables
sh = gc.open_by_url(os.getenv("DRIVE_POINTS"))
Points = sh.worksheet("Points")
Names = sh.worksheet("Names")

# Helper variables and functions
goBackMarkup = InlineKeyboardMarkup([
	[InlineKeyboardButton("⬅ Back to Start", callback_data=START)],
	[InlineKeyboardButton("❌ End", callback_data=END)],
])

def send_typing_action(func):
	"""Sends typing action while processing func command."""
	@wraps(func)
	def command_func(update, context, *args, **kwargs):
		context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
		return func(update, context,  *args, **kwargs)
	return command_func

def postJSON(url, json):
	try:
		r = requests.post(url, json=json)
		r.raise_for_status()
		return r
	except Exception as e:
		logging.error(e)

# Main handlers
def Start(update, context):
	isNewConvo = update.message is not None
	if isNewConvo:
		logger.info("User %s started a conversation.", update.message.from_user.first_name)
		AddToNames(uname=update.message.from_user.username, uid=update.message.from_user.id)

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
		[InlineKeyboardButton("📊 Check Progress", callback_data=PROGRESS)],
		[InlineKeyboardButton("❌ End", callback_data=END)],
	])

	# Send message with text and appended InlineKeyboard
	if isNewConvo:
		update.message.reply_photo(
			photo="AgACAgUAAxkDAAIB1l9TCKTrMMWwU61ekflfLj90yAOuAAKKqjEbdimZVgK1Ii6AzP100QHta3QAAwEAAwIAA20AA6IGAwABGwQ", # fileID
			caption="Hi there future Summiteer! Thank you for signing up for NUSummiteers. Don't forget that you will receive an extra chance in the lucky draw when you refer a friend to sign up for NUSummiteers! Stay tuned for updates here!",
			reply_markup=reply_markup
		)
	else:
		query = update.callback_query
		query.answer()
		query.edit_message_caption(
			caption="Hi there future Summiteer! Thank you for signing up for NUSummiteers. Don't forget that you will receive an extra chance in the lucky draw when you refer a friend to sign up for NUSummiteers!",
			reply_markup=reply_markup
		)

	# Tell ConversationHandler our current state
	return START

@run_async
def AddToNames(uname, uid):
	# find and save ID
	try:
		c = Names.find(uname, in_column=1)
		Names.update_cell(c.row, 3, uid)
	# create ID
	except Exception as e:
		logging.warning(e)
		Names.append_row([uname, None, uid])

def End(update, context):
	query = update.callback_query
	query.answer()
	query.edit_message_caption("🧗 Climb on!")
	return ConversationHandler.END

def Submit(update, context):
	logger.info("I'm in Submit()")
	query = update.callback_query
	query.answer()
	msg = "Upload your activity proof!\n\n🖼 *Photos/Screenshots* - must include elevation gained, timestamp and identification/user ID.\n🎬 *Videos* - must overlay timestamp or include a shot of a phone/watch depicting timestamp at the start of the video AND record complete climb(s) from bottom to top."
	query.edit_message_caption(msg, parse_mode='Markdown', reply_markup=goBackMarkup)
	return SUBMIT

@run_async
def Submitted(update, context):
	logger.info("I'm in Submitted()")
	context.bot.send_message(chat_id=update.effective_chat.id, text="Submission Received!")
	msg = f"Name: *{update.message.from_user.first_name}* `t.me/{update.message.from_user.username}`\nTime: {datetime.now(tz)}"
	context.bot.send_message(chat_id=os.getenv("CHANNEL_ID"), text=msg, parse_mode="Markdown")
	context.bot.forward_message(chat_id=os.getenv("CHANNEL_ID"), from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
	return Start(update, context)

@run_async
def postJSONToSlack(json):
	postJSON(url=os.getenv("SLACK_TOKEN"), json=json)

def Ask(update, context):
	query = update.callback_query
	query.answer()
	query.edit_message_caption("Ask your question below...", reply_markup=goBackMarkup)
	return ASK

def Asked(update, context):
	postJSONToSlack({
		"type": "mrkdwn",
		"text": f"Name: *{update.message.from_user.first_name}* `t.me/{update.message.from_user.username}`\n{update.message.text}",
	})
	context.bot.send_message(chat_id=update.effective_chat.id, text="We'll get back to you soon!")
	return Start(update, context)

@run_async
@send_typing_action
def Progress(update, context):
	query = update.callback_query
	query.answer()
	pts, dt = getPointsAndDatetime(query.from_user.username)
	if pts is None:
		msg = "Your points have not been updated yet"
	else:
		msg = f"Your have gained {pts} points from elevation as at {dt.strftime(dtFormat)}."
	context.bot.send_message(chat_id=query.from_user.id, text=msg)
	return START

def getPointsAndDatetime(uname):
	cells = Points.findall(uname, in_column=1)
	qry = [f"C{i.row}:D{i.row}" for i in cells if i]
	# [[['Fri 8/5/2020 8:00:00', '1']], [['Sun 17/5/2020 8:00:00', '2']]]
	res = Points.batch_get(qry) 
	res = [i[0] for i in res if i]
	res = [(datetime.strptime(d,dtFormat), int(p)) for d,p in res]
	pts = sum(p for _,p in res)
	dt = max(d for d,_ in res)
	logging.info(res)
	return pts, dt

def Unknown(update, context):
	context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

### UNUSED FUNCTIONS (for reference) ###

def postJSONGetPoints(user):
	r = postJSON(json={
		"query": f"SELECT D WHERE A='{user}'",
		"url": os.getenv("DRIVE_POINTS"),
	}, url="https://run.blockspring.com/api_v2/blocks/query-public-google-spreadsheet?&flatten=true")
	# https://run.blockspring.com/api_v2/blocks/query-public-google-spreadsheet?&flatten=true&cache=true&expiry=3600
	try:
		r = r.json()["data"]
		return sum(i["Points"] for i in r)
	except Exception as e:
		logging.error(e)