import logging
import os
from collections import defaultdict
from datetime import timezone, timedelta, datetime
from functools import wraps
from typing import Optional, List, Tuple

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
    ChatAction, Update
from telegram.ext import CallbackContext, JobQueue
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import db
import job

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
tz = timezone(timedelta(hours=8))

# States
ASK = "ask"
LEADERBOARD = "leaderboard"
START, END, SUBMIT, SUBMITTED, ASKED, PROGRESS = map(str, range(6))

# Helper variables and functions
goBackMarkup = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬅ Back to Start", callback_data=START)],
    [InlineKeyboardButton("❌ End", callback_data=END)],
])
START_DT = datetime.fromtimestamp(int(os.getenv("START_TIMESTAMP")), tz=tz)
END_DT = datetime.fromtimestamp(int(os.getenv("END_TIMESTAMP")), tz=tz)
mediaGroups = defaultdict(list)


def send_typing_action(fn):
    @wraps(fn)
    def command_fn(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id,
            action=ChatAction.TYPING)
        return fn(update, context, *args, **kwargs)

    return command_fn


def sidecar(fn):
    @wraps(fn)
    def command_fn(update, context, *args, **kwargs):
        if isAnnouncement(update):
            Announce(context.job_queue, update.channel_post)
            return
        if update.message and str(update.message.chat.id) == os.getenv("ASK_GROUP"):
            return
        if update.channel_post and \
                str(update.channel_post.chat.id) in {os.getenv("ANNOUNCE_CHANNEL"), os.getenv("SUBMISSION_CHANNEL")}:
            return
        save_new_user(update, context)
        return fn(update, context, *args, **kwargs)

    return command_fn


@run_async
def save_new_user(update: Update, context: CallbackContext) -> None:
    if update.message is None:
        return
    if not db.add_new_user(uname=update.message.from_user.username, uid=update.message.from_user.id):
        return
    logger.info("User %s started a conversation.", update.message.from_user.first_name)
    context.bot.forward_message(
        chat_id=update.effective_chat.id,
        from_chat_id=os.getenv("DEBUGGER_ID"),
        message_id=12631  # 654
    )


# Main handlers


@sidecar
def Start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        """Hi Summiteer! Share your summits with us on Instagram @nus_mountaineering and #NUSummiteers to earn an extra chance in the lucky draw!

You can control me with these commands!
For /ask and 📎 (upload), <b>YOU SHOULD RECEIVE</b> a response per submission, eg <code>Submission Received!</code>. If not, please /ask us about it.

/ask <code>Your Question</code>
/leaderboard - See your score and how you stand!
📎 - Upload screenshots/videos/albums!
    - 🖼 Screenshots must include elevation gained, timestamp and identification.
    - 🎬 Videos must start with a shot of a phone/watch depicting timestamp AND record complete climb(s) from bottom to top.
    - ❌ <b>DO NOT</b> submit duplicates, or points will be deducted.""",
        parse_mode='HTML')


#     update.message.reply_photo(
#         photo="AgACAgUAAxkBAAIaGV9qJdUR79nOKU3zMCQ-dfPbFehrAAImqzEbb_lRV41iu9OqGdQfxbpma3QAAwEAAwIAA20AA30rBwABGwQ",
#         # photo="AgACAgUAAxkBAAMMX1umgN2gFleA_S0tFOuqWsypMHgAAm2rMRvT8tlWeV44TIpQ__QP-WBsdAADAQADAgADbQADpaUBAAEbBA",
#         # mir bot
#         caption="""Hi Summiteer! Share your summits with us on Instagram @nus_mountaineering and #NUSummiteers to earn an extra chance in the lucky draw!
#
# You can control me with these commands!
#
# /ask <code>&lt;Your Question&gt;</code>
# /leaderboard - See your score and how you stand!
# 📎 - Upload screenshots/videos/albums!
#     - 🖼 Screenshots must include elevation gained, timestamp and identification.
#     - 🎬 Videos must start with a shot of a phone/watch depicting timestamp AND record complete climb(s) from bottom to top.
#     - ❌ <b>DO NOT</b> submit duplicates, or points will be deducted.""",
#         parse_mode='HTML')


def get_file_name(msg: telegram.Message) -> str:
    try:
        if doc := msg.document:
            return doc.file_name
        if vid := msg.video:
            return vid.file_name
        if anim := msg.animation:
            return anim.file_name
        return ""
    except:
        return ""


@send_typing_action
@sidecar
def Submit(update: telegram.Update, context) -> None:
    if resp := should_reject(update):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=resp,
            reply_to_message_id=update.message.message_id)
        return
    # forward submission to channel
    chan_msg_id = context.bot.forward_message(
        chat_id=os.getenv("SUBMISSION_CHANNEL"),
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id) \
        .message_id
    # send details to channel
    file_name = get_file_name(update.message)
    submission_dt = update.message \
        .date \
        .astimezone(tz=tz) \
        .strftime(db.DtFormat)
    context.bot.send_message(
        chat_id=os.getenv("SUBMISSION_CHANNEL"),
        text=f"Name: *{escape_markdown(update.message.from_user.first_name, version=2)}* t\\.me/{escape_markdown(update.message.from_user.username, version=2)}\nFile Name: {escape_markdown(file_name, version=2)}\nTime: {escape_markdown(submission_dt, version=2)}",
        parse_mode="MarkdownV2",
        reply_to_message_id=chan_msg_id)
    # update db
    db.AddSubmission(
        uname=update.message.from_user.username,
        submittedAt=submission_dt,
        fileName=file_name)
    # respond to user
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Submission Received!",
        reply_to_message_id=update.message.message_id)


def should_reject(update: Update) -> str:
    is_ongoing = START_DT <= datetime.now(tz) <= END_DT
    if not is_ongoing:
        return "Thank you for participating in NUSummiteers! We will only be accepting submissions from 4 Dec to 10 Dec!"
    uname = (update.message if update.message else update.callback_query).from_user.username
    if not db.CanSubmit(uname):
        return "Have you registered at bit.ly/nusummiteers-2? If this is an error, please /ask a question and we will get back to you soon!"
    return ""


@send_typing_action
@sidecar
def Ask(update: Update, context: CallbackContext) -> None:
    try:
        logging.info(context.args)
        assert context.args
    except:
        update.message.reply_text('Usage: /ask <Your Question>')
        return
    # forward to group
    group_msg_id = context.bot.forward_message(
        chat_id=os.getenv("ASK_GROUP"),
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id) \
        .message_id
    context.bot.send_message(
        chat_id=os.getenv("ASK_GROUP"),
        text=f"Name: *{escape_markdown(update.message.from_user.first_name, version=2)}* t\\.me/{escape_markdown(update.message.from_user.username, version=2)}",
        parse_mode="MarkdownV2",
        reply_to_message_id=group_msg_id)
    # reply user
    update.message.reply_text("We'll get back to you soon!", reply_to_message_id=update.message.message_id)


def isAnnouncement(update: Update):
    if update.channel_post is None:
        return False
    if update.channel_post.chat.id != int(os.getenv("ANNOUNCE_CHANNEL")):
        return False
    if update.channel_post.media_group_id in mediaGroups:
        return True
    text = update.channel_post.text
    if text is None:
        text = update.channel_post.caption
    if not (text and text.startswith(os.getenv("ANNOUNCE_PREFIX"))):
        return False
    return True


def getAnnounceText(message: Update.message) -> str:
    text = message.text or message.caption
    if not text:
        return text
    if text.startswith(os.getenv("ANNOUNCE_PREFIX")):
        return text[len(os.getenv("ANNOUNCE_PREFIX")):].strip()
    return text.strip()


def Announce(job_queue: JobQueue, channel_post: Update.channel_post) -> None:
    text = getAnnounceText(channel_post)
    media, err = getMedia(channel_post)
    if err is not None:
        return
    job.ScheduleJob({
        "text": text,
        "media": media,  # pass by reference
    }, job_queue)


def getMedia(message: Update.message) -> Tuple[Optional[List[dict]], Optional[str]]:
    """
    getMedia accounts for 3 cases:
    1. No media
    2. 1 media
    3. >1 media (ie album)

    For case 3, media sent in albums are received by individual updates
       eg `telegram.bot - DEBUG - [<telegram.update.Update object at 0x7f6fb6929c70>, <telegram.update.Update object at 0x7f6fb6925fa0>] `
    These media have a `media_group_id`, and result in 1 call each to the handler
    Fortunately, job scheduling is done AFTER parsing all new updates

    The solution is thus:
    if first media in group
        schedule job by passing a list by reference
    add to media to list

    @param message: telegram message() format
    @return: list of media (by reference), error if scheduled job
    """
    media = []
    if message.photo:
        media.append({"photo": message.photo[-1].file_id})
    if message.video:
        media.append({"video": message.video.file_id})
    if not message.media_group_id:
        return media, None
    existingMediaGroup = message.media_group_id in mediaGroups
    mediaGroups[message.media_group_id].extend(media)
    if existingMediaGroup:
        return None, "Scheduled previous media group"
    return mediaGroups[message.media_group_id], None


def filter_leader(uname: str, stride: int) -> List[Tuple[int, str, str, int]]:
    TOP_K = 3
    res = list(db.GetLeaderboard())
    idx_arr = [i for i, row in enumerate(res) if row[1] == uname]
    if not idx_arr:
        return res[:3]
    idx = idx_arr[0]
    if idx <= TOP_K + stride:
        return res[:idx + stride + 1]
    return res[:3] + [(-1, '', '', -1)] + res[idx - stride: idx + stride + 1]


@send_typing_action
@db.log_error
@sidecar
def Leaderboard(update: Update, context: CallbackContext) -> None:
    STRIDE = 2
    uname = update.message.from_user.username
    res = filter_leader(uname, STRIDE)
    logging.info(res)
    rows = [escape_markdown(format_leaderboard_row(r, uname), version=2) for r in res]
    logging.info(res)
    msg = "Leaderboard\n```" + "\n".join(rows) + "```"
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg, parse_mode="MarkdownV2")


def format_leaderboard_row(row: Tuple[int, str, str, int], uname: str) -> str:
    STRING = "{:>2}. {} {:<18} [{:,}]"
    rank, handle, name, pts = row
    if rank == -1:
        return '...    ...                  ...'
    # map rank to category
    CATS = "🟨⬜🟫⬛️"
    RANKS = [3, 6, 10, 15]
    cat = "  "
    for C, T in zip(RANKS, CATS):
        if rank <= C:
            cat = T
            break
    # truncate name
    if len(name) > 18:
        name = name[:18 - 3] + "..."
    return ('  ' if handle == uname else '') + STRING.format(rank, cat, name, pts)
