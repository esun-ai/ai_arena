# -*- coding:utf-8 -*-
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
from datetime import datetime
from src.check_end_signal import Check_End_Signal
from src.logger import logger
from src.send_leaderboard import Send_Leaderboard

env = os.environ['ENV']
official_start_date = datetime.strptime(os.environ['OFFICIAL_START_DATE'], "%Y-%m-%d").date()
official_end_date = datetime.strptime(os.environ['OFFICIAL_END_DATE'], "%Y-%m-%d").date()

def start_leaderboard():
    current_time = datetime.now()
    try:
        if current_time.date() < official_start_date or current_time.date() > official_end_date:
            logger.info({
                "message": "[Leaderboard] It's not official time.",
                "trigger": "Leaderboard",
                "ENV": env,
                "timestamp": str(current_time)})
        else:
            signal_obj = Check_End_Signal(current_time)
            while True:
                start_time = datetime.now()
                if not signal_obj.check():
                    logger.info({
                        "message": "[Leaderboard] Daily task is not finished yet. Stop sending leaderboard.",
                        "trigger": "Leaderboard",
                        "ENV": env,
                        "timestamp": str(start_time)})
                    time.sleep(300)
                else:
                    logger.info({
                        "message": "[Leaderboard] Daily task finished. Start calculating scores.",
                        "trigger": "Leaderboard",
                        "ENV": env,
                        "timestamp": str(start_time)})
                    sender = Send_Leaderboard(current_time)
                    sender.send()
                    end_time = datetime.now()
                    spent_time = end_time - start_time
                    spent_time = spent_time.total_seconds()
                    logger.info({
                        "message": "[Leaderboard] Finish sending leaderboard",
                        "trigger": "Leaderboard",
                        "ENV": env,
                        "timestamp": str(end_time),
                        "spent_time": str(spent_time) + " secs"})
                    break
    except Exception as error:
        logger.error({
            "message": f"[Leaderboard] Error: {error}",
            "trigger": "Leaderboard",
            "ENV": env,
            "timestamp": str(datetime.now())})

if __name__ == '__main__':
    start_leaderboard()