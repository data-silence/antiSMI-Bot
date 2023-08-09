from imports.imports import bot, BlockingScheduler, threading
from scripts.senders import sending_fresh_news, sending_past_news

"""
This is the control module for launching and interacting between the constituent parts of the Bot.

When the script is started, two threads are executed: 
1. permanent bot operation (uses handlers.py and processor.py from scripts directory)
2. periodic user mailings (uses senders.py and time_machine.py from scripts directory)  

* handlers.py   -   basic bot functions and its handlers
* processors.py -   set of auxiliary functions that process news and assist in the work of handlers
* senders.py    -   functions for managing periodic digest mailings
* time_machine  -   set of classes to organize a "time machine", allowing you to get annual news from the past for each day 



Это управляющий модуль для запуска и взаимодействия между составляющими частями Бота.
При запуске скрипта выполняются два потока: поток текущей работы бота и поток периодических пользовательских рассылок 
"""


def run_bot():
    """
    The thread of current work of the bot
    """
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception:
            pass


def run_sending():
    """
    The thread to send subscribers digests and news from the "time machine"
    Поток для рассылки подписчикам дайджестов и новостей от "машины времени"
    """
    scheduler = BlockingScheduler(timezone='Europe/Moscow')
    scheduler.add_job(sending_past_news, 'cron', hour=6)
    scheduler.add_job(sending_fresh_news, 'cron', [1], hour=10)
    scheduler.add_job(sending_fresh_news, 'cron', [2], hour=14)
    scheduler.add_job(sending_fresh_news, 'cron', [3], hour=18)
    scheduler.add_job(sending_fresh_news, 'cron', [4], hour=22)
    scheduler.start()


if __name__ == "__main__":
    try:
        sending_thread = threading.Thread(target=run_sending)
        sending_thread.start()

        bot_thread = threading.Thread(target=run_bot)
        bot_thread.start()
        bot_thread.join()

    except Exception:
        pass
