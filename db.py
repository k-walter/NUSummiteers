import logging
import os
from collections import defaultdict, OrderedDict
from functools import wraps
from typing import Tuple, Iterable

import gspread
from telegram.ext.dispatcher import run_async

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
gc = gspread.service_account(filename='client_secret.json')
sh = gc.open_by_url(os.getenv("SHEET_URL"))

# Global variables
DtFormat = "%a %d/%m/%Y %H:%M:%S"
Points = sh.worksheet("Submissions")
Names = sh.worksheet("Names")
# Poll = sh.worksheet("Poll")
Leaderboard = sh.worksheet("Leaderboard")


# Helper
def log_error(func):
    @wraps(func)
    def command_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(e)

    return command_func


cache = OrderedDict()


def lru_cache(func, maxSize=128):
    @wraps(func)
    def command_func(*args):
        # cache hit
        if args in cache:
            cache.move_to_end(args)
            return cache[args]
        # cache miss
        result = func(*args)
        if not result:  # False
            return result
        # save True response
        cache[args] = result
        # lru
        if len(cache) > maxSize:
            cache.popitem(last=False)
        return result

    return command_func


# Main functions


def add_new_user(uname: str, uid: int) -> bool:
    # find and save ID
    try:
        c = Names.find(uname, in_column=1)
        if Names.cell(c.row, 3).value == str(uid):
            return False
        logging.info(Names.update_cell(c.row, 3, uid))
    # create ID
    except:
        logging.info(Names.append_row([uname, None, uid]))
    return True


@log_error
def GetLeaderboard() -> Iterable[Tuple[int, str, str, int]]:
    rows = range(3, 3 + 100 - 1)
    qry = [f"L{i}:O{i}" for i in rows]
    res = Leaderboard.batch_get(qry)
    for row in res:
        try:
            [[rank, pts, handle, name]] = row
            if handle:
                yield int(rank), handle, name, float(pts)
        except:
            continue
    # formattedRes = [(int(rank), name, int(pts))
    #                 for [[rank, pts, handle, name]] in res if handle]
    # return formattedRes






@run_async
@log_error
def SavePoll(uname, pid):
    Poll.append_row([uname, None, pid])


@run_async
@log_error
def UpdatePoll(pid, option):
    c = Poll.find(pid, in_column=3)
    Poll.update(f"D{c.row}", option)


@log_error
@lru_cache
def CanSubmit(uname: str) -> bool:
    MakeUnique()
    cell = Names.find(uname, in_column=1)
    out = Names.get(f"D{cell.row}")[0][0]
    return out == "YES"


@log_error
def AddSubmission(uname: str, submittedAt: str, fileName: str) -> None:
    Points.append_row([uname, None, submittedAt, fileName])  # table_range="A1"


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
            'values': [mval], })

        # delete extra rows
        for i in rows[1:]:
            Names.delete_rows(i + 2)

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
