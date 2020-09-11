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
		res = [i[0] for i in res if i]
		res = [(datetime.strptime(d,DtFormat), int(p)) for d,p in res]
		pts = sum(p for _,p in res)
		dt = max(d for d,_ in res)
		return pts, dt
	except Exception as e:
		logging.warning(e)
		return None, None

def MakeUnique():
	try:
		# get all rows
		db = handler.Names.batch_get(["A2:C"])[0]

		# get unique handlers
		# 0 in rows ---> 2 in db
		users = defaultdict(list)
		for i, row in enumerate(db):
			if len(row) < 1:
				continue
			users[row[0].lower()].append(i)

		# combine same handlers
		updates = list()
		for uname, rows in users.items():
			if len(rows) == 1:
				continue

			# keep longest name, uid
			name, uid = "", ""
			for i in rows:
				row = db[i]
				if len(row) >= 2 and len(row[1]) > len(name):
					name = row[1]
				if len(row) >= 3 and len(row[2]) > len(uid):
					uid = row[2]

			# delete and save for update
			i = rows[0] + 2
			updates.append({
				'range': f"B{i}:C{i}",
				'values': [[name, uid]],
			})
			for i in rows[1:]:
				handler.Names.delete_rows(i+2)

		# update unique handlers
		handler.Names.batch_update(updates, value_input_option="USER_ENTERED")

	except Exception as e:
		logging.error(e)

def Broadcast(fn):
	MakeUnique()
	fn(69761990)

	# TODO send to all
	return
	ids = handler.Names.get("C2:C")
	ids = [int(i[0]) for i in ids if i]
	for cid in ids:
		fn(cid)
