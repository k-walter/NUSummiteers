import os
import db
import requests
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

# States
START, END, SUBMIT, SUBMITTED, ASK, ASKED, PROGRESS, LEADERBOARD = map(
    str, range(8))

# Helper variables and functions
goBackMarkup = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅ Back to Start", callback_data=START)],
    [InlineKeyboardButton("❌ End", callback_data=END)],
])


def send_typing_action(func):
    """Sends typing action while processing func command."""
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id,
            action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)
    return command_func


@db.log_error
def postJSON(url, json):
    r = requests.post(url, json=json)
    r.raise_for_status()
    return r


@run_async
def postJSONToSlack(json):
    postJSON(url=os.getenv("SLACK_CHANNEL"), json=json)

# Main handlers


def Start(update, context):
    isNewConvo = update.message is not None
    if isNewConvo:
        logger.info("User %s started a conversation.",
                    update.message.from_user.first_name)
        db.AddToNames(uname=update.message.from_user.username,
                      uid=update.message.from_user.id)

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
        [InlineKeyboardButton("🧗 Check Progress", callback_data=PROGRESS)],
        [InlineKeyboardButton("📊 Check Leaderboard",
                              callback_data=LEADERBOARD)],
        [InlineKeyboardButton("❌ End", callback_data=END)],
    ])

    # Send message with text and appended InlineKeyboard
    if isNewConvo:
        update.message.reply_photo(
            # photo="AgACAgUAAxkBAAIaGV9qJdUR79nOKU3zMCQ-dfPbFehrAAImqzEbb_lRV41iu9OqGdQfxbpma3QAAwEAAwIAA20AA30rBwABGwQ",  # fileID
            photo="AgACAgUAAxkBAAMMX1umgN2gFleA_S0tFOuqWsypMHgAAm2rMRvT8tlWeV44TIpQ__QP-WBsdAADAQADAgADbQADpaUBAAEbBA",  # mir bot
            caption="Hi Summiteer! Remember to share your activity with us on Instagram @nus_mountaineering and #NUSummiteers! You will earn an extra chance in the lucky draw daily when you tag us! Stay tuned for updates here! Also, check out our site: https://nus-mir.com/nusummiteers/",
            reply_markup=reply_markup)
    else:
        query = update.callback_query
        query.answer()
        query.edit_message_caption(
            caption="Hi Summiteer! 📣Share pictures and/or videos of their activities of yourself attempting NUSummiteers on our Instagram Story @nus_mountaineering, and use the hashtag #NUSummiteers to earn an extra chance for the lucky draw per day! Stay tuned for updates here! Also, check out our site: https://nus-mir.com/nusummiteers/",
            reply_markup=reply_markup)

    # Tell ConversationHandler our current state
    return START


@run_async
def UpdatePoll(update, context):
    poll = update.poll
    pid = poll.id
    for opt in poll.options:
        cnt = opt.voter_count
        if cnt == 0:
            continue
        # update selected option
        text = opt.text
        db.UpdatePoll(pid, text)
        return


def End(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_caption("🧗 Climb on!")
    return ConversationHandler.END


@send_typing_action
def Submit(update, context):
    query = update.callback_query
    query.answer()
    if RejectSubmission(update, context):
        return START
    msg = "Upload your activity proof!\n\n🖼 *Photos/Screenshots* - must include elevation gained, timestamp and identification/user ID.\n🎬 *Videos* - must overlay timestamp or include a shot of a phone/watch depicting timestamp at the start of the video AND record complete climb(s) from bottom to top.\n📁 You can now upload many submissions as an album!\n\n❌ *DO NOT* submit duplicates. Repeated occurrences of duplicate submissions will lead to deduction of points.\n✅ We encourage you to caption your submissions with *date, time*, eg `20/9 08:40`. This can help you double check your submissions to avoid duplicates!"
    query.edit_message_caption(
        msg,
        parse_mode='Markdown',
        reply_markup=goBackMarkup)
    return SUBMIT


@send_typing_action
def Submitted(update, context):
    if RejectSubmission(update, context):
        return START
    # forward submission to channel
    msg = context.bot.forward_message(
        chat_id=os.getenv("CHANNEL_ID"),
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id)
    # send timestamp to channel
    dt = update.message \
        .date \
        .astimezone(tz=tz) \
        .strftime(db.DtFormat)
    text = f"Name: *{update.message.from_user.first_name}* `t.me/{update.message.from_user.username}`\nTime: {dt}"
    context.bot.send_message(
        chat_id=os.getenv("CHANNEL_ID"),
        text=text,
        parse_mode="Markdown",
        reply_to_message_id=msg.message_id,)
    # update db
    db.AddSubmission(
        uname=update.message.from_user.username,
        submittedAt=dt,)
    # respond to user
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Submission Received!",
        reply_to_message_id=update.message.message_id,)
    return SUBMIT


def RejectSubmission(update, context):
    # get username, original message_id
    reply = None
    if update.message:
        uname = update.message.from_user.username
        reply = update.message.message_id
    else:
        query = update.callback_query
        uname = query.from_user.username
    # send warning
    if db.CanSubmit(uname):
        return False
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, we are not accepting submissions from unregistered persons. If this is an error, please `Ask A Question` and we will get back to you soon.",
        parse_mode="Markdown",
        reply_to_message_id=reply,)
    return True


def Ask(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_caption(
        "Ask your question below...",
        reply_markup=goBackMarkup)
    return ASK


def Asked(update, context):
    postJSONToSlack({
        "type": "mrkdwn",
        "text": f"Name: *{update.message.from_user.first_name}* `t.me/{update.message.from_user.username}`\n{update.message.text}",
    })
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="We'll get back to you soon!")
    return Start(update, context)


@run_async
@send_typing_action
def Progress(update, context):
    query = update.callback_query
    query.answer()
    pts, dt = db.GetPointsAndDate(query.from_user.username)
    if pts is None:
        msg = "Your points have not been updated yet"
    else:
        msg = f"Your points from elevation gained is {pts} points based on your submission as at {dt.strftime(db.DtFormat)}."
    context.bot.send_message(chat_id=query.from_user.id, text=msg)
    return START


def Unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command. Type /start to begin.")


@run_async
@send_typing_action
@db.log_error
def Leaderboard(update, context):
    query = update.callback_query
    query.answer()
    res = db.GetLeaderboard(20)
    rows = [formatLeader(r) for r in res]
    msg = "<pre>Leaderboard\n" + "\n".join(rows) + "</pre>"
    context.bot.send_message(chat_id=query.from_user.id,
                             text=msg, parse_mode="HTML")
    return START


def formatLeader(row):
    STRING = "{:>2}. {} {:<20} [{:,}]"
    print(row)
    rank, name, pts = row
    # map rank to category
    CATS = "🟨⬜🟫⬛️"
    RANKS = [3, 6, 10, 15]
    cat = "  "
    for C, T in zip(RANKS, CATS):
        print(row, C, T, rank <= C)
        if rank <= C:
            cat = T
            break
    # truncate name
    if len(name) > 20:
        name = name[:20-3] + "..."
    return STRING.format(rank, cat, name, pts)
