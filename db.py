import os
import gspread
import logging
from functools import wraps
from datetime import datetime
from collections import defaultdict, OrderedDict
from telegram.ext.dispatcher import run_async

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
gc = gspread.service_account(filename='client_secret.json')
sh = gc.open_by_url(os.getenv("DRIVE_URL"))

# Global variables
DtFormat = "%a %d/%m/%Y %H:%M:%S"
Points = sh.worksheet("Points")
Names = sh.worksheet("Names")
Poll = sh.worksheet("Poll")

def log_error(func):
	@wraps(func)
	def command_func(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Exception as e:
			logging.error(e)
	return command_func

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

def GetPointsAndDate(uname):
	try:
		cells = Points.findall(uname, in_column=1)
		qry = [f"C{i.row}:D{i.row}" for i in cells if i]
		# [[['Fri 8/5/2020 8:00:00', '1']], [['Sun 17/5/2020 8:00:00', '2']]]
		res = Points.batch_get(qry) 
		res = [i[0] for i in res if i and i[0][1]]
		res = [(datetime.strptime(d,DtFormat), int(p)) for d,p in res]
		pts = sum(p for _,p in res)
		dt = max(d for d,_ in res)
		return pts, dt
	except Exception as e:
		logging.warning(e)
		return None, None

def GetSIDFromTID(tid):
	try:
		c = Names.find(tid, in_column=3)
		return Names.get(f"D{c.row}"), True
	except Exception as e:
		return None, False

def GetTIDFromSID(sid):
	try:
		c = Names.find(si, in_column=4)
		return Names.get(f"C{c.row}"), True
	except Exception as e:
		logging.error(e)
		return None, False

@log_error
def SaveSIDWithTID(tid, sid):
	c = Names.find(tid, in_column=3)
	Names.update(f"D{c.row}", sid)

@run_async
@log_error
def SavePoll(uname, pid):
	Poll.append_row([uname, None, pid])

@run_async
@log_error
def UpdatePoll(pid, option):
	c = Poll.find(pid, in_column=3)
	Poll.update(f"D{c.row}", option)

cache = OrderedDict()
def lru_cache(func, maxSize=128):
	@wraps(func)
	def command_func(*args):
		# cache hit
		if args in cache:
			cache.move_to_end(args)
			return cache[args]
		# call function
		result = func(*args)
		if not result: # False
			return result
		# save True response
		cache[args] = result
		# lru
		if len(cache) > maxSize:
			cache.popitem(last=False)
		return result
	return command_func

@log_error
@lru_cache
def CanSubmit(uname):
	MakeUnique()
	c = Names.find(uname, in_column=1)
	out = Names.get(f"E{c.row}")[0][0]
	return out == "YES"

@log_error
def AddSubmission(uname, submittedAt):
	Points.append_row([uname, None, submittedAt])

@log_error
def MakeUnique():
	# get all rows
	db = Names.batch_get(["A2:E"])[0]

	# get unique handlers
	# 0 in rows ---> 2 in db
	users = defaultdict(list)
	ncol = 0
	for i, row in enumerate(db):
		if len(row) < 1:
			continue
		users[row[0].lower()].append(i)
		ncol = max(ncol, len(row))

	# combine same handlers
	updates = list()
	for uname, rows in users.items():
		if len(rows) == 1:
			continue

		# keep longest name, tid, sid
		mval = [""] * (ncol - 1)
		name, uid = "", ""
		for i in rows:
			row = db[i]
			for j, val in enumerate(row[1:], 0):
				if len(val) > len(mval[j]):
					mval[j] = val

		# update combined values
		i = rows[0] + 2
		updates.append({
			'range': f"B{i}:E{i}",
			'values': [mval],
		})

		# delete extra rows
		for i in rows[1:]:
			Names.delete_rows(i+2)

	# update unique handlers
	Names.batch_update(updates, value_input_option="USER_ENTERED")

@log_error
def GetUnique():
	MakeUnique()
	tid = Names.get("C2:C")
	tid = [int(i[0]) for i in tid if i]
	return tid

if __name__ == "__main__":
	MakeUnique()
