import os
import db
import logging
from slack import RTMClient
from slack.errors import SlackApiError
from telegram.ext.dispatcher import run_async

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#### SLACK ####

# subscribe to thread reply
	# get slack -> id
	# send_message to id

# CreateOrReply
	# check if id -> slack exists
	# if not
		# save id -> slack
		# "we'll get back to you soon"
	# reply in slack
		# need channel id, ts of parent


#### TELEGRAM ####

# If convo
	# CreateOrReply thread

class SlackBot:
	def __init__(self, tbot):
		self.tbot = tbot
		self.sc = RTMClient(token=os.getenv("SLACK_TOKEN"))

		self.sc.start()

	def SendMessage(self, json):
		try:
			# rtm_client = payload['rtm_client']
			# resp = rtm_client.chat_postMessage(
			# 	channel=os.getenv("SLACK_CHANNEL"),
			# 	text=text,
			# 	thread_ts=thread_ts,
			# )
			r = requests.post(os.getenv("SLACK_CHANNEL"), json=json)
			r.raise_for_status()
			return r
		except SlackApiError as e:
			assert e.response["ok"] is False
			assert e.response["error"]
			logging.error(e.response["error"])
		except Exception as e:
			logging.error(e)

	@run_async
	def TelegramToSlack(self, update, context):
		tid = update.effective_chat.id
		sid, ok = db.GetSIDFromTID(tid)
		if ok:
			self.SendMessage({
				"thread_ts": sid,
				"type": "mrkdwn",
				"text": f"{update.message.text}",
			})
			return

		# reply to telegram, send to slack
		context.bot.send_message(chat_id=tid, text="We'll get back to you soon!")
		resp = self.SendMessage({
			"type": "mrkdwn",
			"text": f"{update.message.text}",
		})
		if not resp:
			return

		# save SID
		logging.info(resp)
		sid = 123
		db.SaveSIDWithTID(tid, str(sid))

	@RTMClient.run_on(event='message')
	def SlackToTelegram(self, **payload):
		d = payload["data"]
		if d.get("subtype", []) != "message_replied":
			return

		# get telegram chat_id
		sid = d["message"]["thread_ts"]
		tid, ok = GetTIDFromSID(sid)
		if not ok:
			return

		# pm telegram msg
		msg = d["message"]["text"]
		self.tbot.send_message(chat_id=tid, text=msg, parse_mode="Markdown")

if __name__ == "__main__":
	bot = SlackBot(None)