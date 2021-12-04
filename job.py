import logging
import os
from datetime import timezone, timedelta, datetime

import yaml
from telegram import InputMediaPhoto, InputMediaVideo
from telegram.ext.dispatcher import run_async

import db

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
tz = timezone(timedelta(hours=8))
test = os.getenv("TEST") != "false"


def Broadcast(fn):
    logging.info(f"Broadcasting {fn}")
    tids = db.GetUnique()
    if not tids:
        return

    if test:
        fn(os.getenv("DEBUGGER_ID"))
        return

    for tid in tids:
        try:
            fn(tid)
        except Exception as e:
            logging.error(e)


def Schedule(job_queue):
    # job_queue.run_once(SendMessage("Ready? Climb on!"), 0)
    with open("schedule.yml") as f:
        jobs = yaml.load(f, Loader=yaml.FullLoader)
    for job in jobs:
        ScheduleJob(job, job_queue)
        if test:
            return


@db.log_error
@run_async
def ScheduleJob(job, job_queue):
    text = job.get("text", None)
    dt, err = getDatetime(job)
    if err is not None:
        return

    # if test:
    #     dt = 3

    if job.get("options", None):
        job_queue.run_once(SendPoll(job["options"], text), dt)

    elif job.get("media", None):
        media = job["media"]
        if len(media) == 1:
            job_queue.run_once(SendMedia(media[0], text), dt)
        else:
            job_queue.run_once(SendMediaGroup(media, text), dt)

    else:
        job_queue.run_once(SendMessage(text), dt)


def getDatetime(job):
    if "datetime" not in job:
        return 0, None
    dt = datetime(*job["datetime"], tzinfo=tz)
    isOverdue = dt < datetime.now(tz)
    if isOverdue:
        return None, "overdue"
    return dt, None


def SendMessage(text):
    def callback(context):
        def fn(tid): return context.bot.send_message(
            chat_id=tid,
            text=text,
            parse_mode="HTML",)
        Broadcast(fn)
    return callback


def SendMedia(media, text):
    if "photo" in media:
        return SendPhoto(media, text)
    if "video" in media:
        return SendVideo(media, text)


def SendMediaGroup(media, text):
    parseMode = "HTML"
    out = list()
    for m in media:
        if "photo" in m:
            i = InputMediaPhoto(
                media=m["photo"], caption=text, parse_mode=parseMode)
        elif "video" in m:
            i = InputMediaVideo(
                media=m["video"], caption=text, parse_mode=parseMode)
        else:
            continue

        out.append(i)
        # set caption for first media only
        text, parseMode = None, None

    def callback(context):
        def fn(tid): return context.bot.send_media_group(
            chat_id=tid,
            media=out
        )
        Broadcast(fn)
    return callback


def SendPhoto(media, text):
    def callback(context):
        def fn(tid): return context.bot.send_photo(
            chat_id=tid,
            photo=media["photo"],
            caption=text,
            parse_mode="HTML",
        )
        Broadcast(fn)
    return callback


def SendVideo(media, text):
    def callback(context):
        def fn(tid): return context.bot.send_video(
            chat_id=tid,
            video=media["video"],
            caption=text,
            parse_mode="HTML",
        )
        Broadcast(fn)
    return callback


def SendPoll(options, text):
    def callback(context):
        def fn(tid):
            msg = context.bot.send_message(
                chat_id=tid,
                text=text,
                parse_mode="HTML",
            )
            msg = context.bot.send_poll(
                reply_to_message_id=msg.message_id,
                chat_id=tid,
                question="Pick 1 Option",
                options=options,
            )
            # bot only returns poll id
            # save uname --> poll id
            uname = msg["chat"]["username"]
            pid = msg["poll"]["id"]
            db.SavePoll(uname, pid)
        Broadcast(fn)
    return callback
