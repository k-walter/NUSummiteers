import os
import gspread
import logging
from datetime import datetime
from collections import defaultdict
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

def SaveSIDWithTID(tid, sid):
	try:
		c = Names.find(tid, in_column=3)
		Names.update(f"D{c.row}", sid)
	except Exception as e:
		logging.error(e)

@run_async
def SavePoll(uname, pid):
	try:
		Poll.append_row([uname, None, pid])
	except Exception as e:
		logging.error(e)

@run_async
def UpdatePoll(pid, option):
	try:
		c = Poll.find(pid, in_column=3)
		Poll.update(f"D{c.row}", option)
	except Exception as e:
		logging.error(e)

def MakeUnique():
	try:
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

	except Exception as e:
		logging.error(e)

def GetUnique():
	try:
		tid = Names.get("C2:C")
		tid = [int(i[0]) for i in tid if i]
		return tid
	except Exception as e:
		logging.error(e)

if __name__ == "__main__":
	MakeUnique()
