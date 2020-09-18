import os
import db
import yaml
import handler
from telegram import InputMediaPhoto, InputMediaVideo
from datetime import timezone, timedelta, datetime
import logging

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
tz = timezone(timedelta(hours=8))
test = False

def Broadcast(fn):
	logging.info(f"Broadcasting {fn}")
	db.MakeUnique()
	tids = db.GetUnique()
	if not tids:
		return

	if test:
		fn(69761990)
		return

	for tid in tids:
		try:
			fn(tid)
		except Exception as e:
			logging.error(e)


def Schedule(job_queue):
	with open("schedule.yml") as f:
		jobs = yaml.load(f, Loader=yaml.FullLoader)
	for job in jobs:
		try:
			text = job.get("text", "")
			dt = datetime(*job["datetime"], tzinfo=tz)
			if test:
				dt = 5

			# text message
			if "media" not in job:
				job_queue.run_once(SendMessage(text), dt)
				continue
			media = job["media"]

			# media message
			if len(media) == 1:
				job_queue.run_once(SendMedia(media[0], text), dt)
				continue

			# media group message
			job_queue.run_once(SendMediaGroup(media, text), dt)

		except Exception as e:
			logging.error(e)

# [
# 	{'datetime': [2020, 9, 19, 12], 'text': 'Welcome to NUSummiteers! We hope you are as excited as we are as you embark on a one-week challenge to clock as much elevation gain as you can! Remember: the only competitor you’re up against is yourself. All the best, the summit awaits!'},
# 	{'datetime': [2020, 9, 19, 19], 'text': 'How did you fare for Day 1? Any chance you visited Bukit Timah Hill to clock some mileage? If not, did you know that *Bukit Timah Hill (164m)* is the highest natural point in Singapore, and also where NUS Mountaineering holds our loaded stair-climb training? If you’ve yet to visit it, why not schedule a trip down and get a good workout in too! Check out the routes available here: bit.ly/NUSummiteers-BTH.', 'media': [
# 		{'photo': 'AgACAgUAAxkBAAIHll9k_UmTU2NMpeY8B4fVeJf0aI-cAAINrTEb4t0oVxqZZ6GbpRGfEJpLbHQAAwEAAwIAA20AA4v9AQABGwQ'},
# 		{'photo': 'AgACAgUAAxkBAAIHl19k_VNdURcha9hCaZ-gI-FCgSlQAAIOrTEb4t0oV2-5AAE19k2SiJLXAAFsdAADAQADAgADbQADQxUDAAEbBA'}
# 		]},
# ]

def SendMessage(text):
	def callback(context):
		fn = lambda tid: context.bot.send_message(
			chat_id=tid,
			text=text,
			parse_mode="Markdown",
		)
		Broadcast(fn)
	return callback

def SendMedia(media, text):
	if "photo" in media:
		return SendPhoto(media, text)
	if "video" in media:
		return SendVideo(media, text)

def SendMediaGroup(media, text):
	parseMode = "Markdown"
	out = list()
	for m in media:
		if "photo" in m:
			i = InputMediaPhoto(media=m["photo"], caption=text, parse_mode=parseMode)
		elif "video" in m:
			i = InputMediaVideo(media=m["video"], caption=text, parse_mode=parseMode)
		else:
			continue

		out.append(i)
		# set caption for first media only
		text, parseMode = None, None

	def callback(context):
		fn = lambda tid: context.bot.send_media_group(
			chat_id=tid,
			media=out
		)
		Broadcast(fn)
	return callback

def SendPhoto(media, text):
	def callback(context):
		fn = lambda tid: context.bot.send_photo(
			chat_id=tid,
			photo=media["photo"],
			caption=text,
			parse_mode="Markdown",
		)
		Broadcast(fn)
	return callback

def SendVideo(media, text):
	def callback(context):
		fn = lambda tid: context.bot.send_video(
			chat_id=tid,
			video=media["video"],
			caption=text,
			parse_mode="Markdown",
		)
		Broadcast(fn)
	return callback

### UNUSED FUNCTIONS ###

def Fact19Sep12(context):
	fn = lambda tid: context.bot.send_message(
		chat_id=tid,
		text="Welcome to NUSummiteers! We hope you are as excited as we are as you embark on a one-week challenge to clock as much elevation gain as you can! Remember: the only competitor you’re up against is yourself. All the best, the summit awaits!",
		parse_mode="Markdown",
	)
	Broadcast(fn)

def Referral(context):
	# to get from yaml
	fn = lambda tid: context.bot.send_media_group(
		chat_id=tid,
		media=[
		InputMediaPhoto(
			caption="We are only 3 days away from the start of NUSummiteers!!\n\nMany prizes on the leaderboard are to be won! You can win up to $100 Outdoor Life vouchers and purchase exclusive gears from Patagonia, The North Face, Black Diamond and more! (Register at: bit.ly/NUSummiteers)\n\nDo check out the FAQ at bit.ly/NUSummiteersFAQ. If you still have any queries, do send them in through this bot. :)",
			media="AgACAgUAAxkBAAIFXF9dqd9aeEUvPoYWyeviSZZoK5bhAAJxqjEba_fwViJZ5tWpBNJBhD_KbHQAAwEAAwIAA20AA112AAIbBA",
		),
		InputMediaPhoto("AgACAgUAAxkBAAIFXV9dqd9HzJQOupkXJsQvq39IbG-7AAJyqjEba_fwVs0drrBMMHLawqzFbHQAAwEAAwIAA20AA_JzAAIbBA"),
		InputMediaPhoto("AgACAgUAAxkBAAIFXl9dqd8acaHVJWit2z5e-INWjOiLAAJzqjEba_fwVnWEt6Ahq4a0uWkFbHQAAwEAAwIAA20AAyfPAgABGwQ"),
		]
	)
	Broadcast(fn)

def PreEvent(context):
	fn = lambda tid: context.bot.send_media_group(
		chat_id=tid,
		media=[
		InputMediaPhoto(
			caption="🏝🌅Recess week is almost here! That means NUSummiteers is starting very soon! \n\n📣Do take note that the your daily leaderboard points will be *tallied as of 9 pm* and *updated as of 10 pm*. Submissions thereafter, will be counted towards the points tally of the next day! Your points will be accumulated throughout the whole event and prizes will be given based on the final leaderboard. Do practice graciousness and keep the submissions coming in consistently as our team will be reviewing every single submission.\n\n🌄For more information visit our T&C at bit.ly/NUSummiteersTandCs. We have been addressing your enquiries at bit.ly/NUSummiteersFAQ too! ☺️",
			parse_mode="Markdown",
			media="AgACAgUAAxkBAAIGy19kEIMzmIC5Me6GOghwmdmTIAVFAAJAqzEbGaUgVyNc1FUC1OLdSkzNbHQAAwEAAwIAA20AA2StAAIbBA",
		),
		InputMediaPhoto("AgACAgUAAxkBAAIGzF9kEI21fGEw-F3XUhHIPGm30RUwAAJBqzEbGaUgV__SVx9jqV-f-L-ObHQAAwEAAwIAA20AA_XuAAIbBA"),
		InputMediaVideo("BAACAgUAAxkBAAIGzV9kEJlWLyWnymWw7FwMdmC0ZGolAAKTAQACGaUgV-WFqFfjIZqSGwQ"),
		]
	)
	Broadcast(fn)
