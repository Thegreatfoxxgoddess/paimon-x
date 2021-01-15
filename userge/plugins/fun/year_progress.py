# by @deleteduser420
import datetime
import math

from userge import userge


@userge.on_cmd("yp$", about={"header": "Year Progress Bar"})
async def progresss(message):
    x = datetime.datetime.now()
    day = int(x.strftime("%j"))
    total_days = 365 if x.year % 4 != 0 else 366  # Haha Yes Finally
    percent = math.trunc(day / total_days * 100)
    await message.edit(make_bar(percent) + f" {percent}%")

# the following function has been taken from @saitamarobot to be found on tg
def make_bar(per):
    done = round(per / 5)
    return "▓" * done + "░" * (20 - done)
