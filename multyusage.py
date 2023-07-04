import asyncio
import json
import logging
import time

from main import main as create_bot
from threading import Thread

SOURCE = 'constructor/bots.json'

logging.basicConfig(
    filename='logs.txt',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)
logger = logging.getLogger(__name__)


def run_bot(bot_config):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    r_interval = bot_config['r_interval'][0] * \
                 (1 if bot_config['r_interval'][1] == 'секунды' else 60
                 if bot_config['r_interval'][1] == 'минуты' else (60 * 60))

    c_timeout = bot_config['c_timeout'][0] * \
                (1 if bot_config['c_timeout'][1] == 'секунды' else 60
                if bot_config['c_timeout'][1] == 'минуты' else (60 * 60))

    bot = create_bot(telegram_token=bot_config['telegram_token'],
                     company_name=bot_config['medorg_name'],
                     company_id=bot_config['medorg_id'],
                     reminder_interval=r_interval,
                     conversation_timeout=c_timeout,
                     cell_number_limit=bot_config['cell_number_limit'])
    bot.run_polling()


def main():
    threads = []

    with open(SOURCE) as file:
        data = json.load(file)

    for i in data:
        thread = Thread(target=run_bot, args=(i,))
        threads.append(thread)

    for thread in threads:
        thread.start()


if __name__ == '__main__':
    main()
    while True:
        time.sleep(1)
