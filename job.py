import os
import yaml
import handler
from datetime import timezone, timedelta, datetime
import logging

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
tz = timezone(timedelta(hours=8))

def Broadcast(fn):
	ids = handler.Names.get("C2:C")
	ids = [int(i[0]) for i in ids if i]
	for cid in ids:
		fn(cid)

def Fact(context):
	# to get from yaml
	Broadcast(lambda cid: context.bot.send_message(chat_id=cid, text="Interesting fact"))

def Leaderboard():
	return

def Progress():
	return

def Leaderboard():
	return

def FAQ():
	return
