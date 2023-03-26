import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters

from data import BOT_TOKEN, COMPANY_NAME, DOCTORS


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


kb_syms = [['/start']]
kb = ReplyKeyboardMarkup(kb_syms, one_time_keyboard=True, resize_keyboard=True)
doctors_lst = []
for i in range(1, len(DOCTORS) + 1):
    if i % 2 != 0:
        doctors_lst.append([DOCTORS[i - 1]])
    else:
        doctors_lst[-1].append(DOCTORS[i - 1])
doctors_lst[-1].append('/cancel') if len(doctors_lst[-1]) == 1 else doctors_lst.append(['/cancel'])
dctr = ReplyKeyboardMarkup(doctors_lst, one_time_keyboard=True, resize_keyboard=True)


async def misunderstanding(update, context):
    await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.', reply_markup=kb)


async def begining(update, context):
    await update.message.reply_html(f"""\tЗдравствуйте! Я - бот для записи на прием в компании {COMPANY_NAME}
    \nВыберите один из вариантов, предоставленных ниже.""", reply_markup=dctr)


async def cancellation(update, context):
    await update.message.reply_text('До скорой встречи! \nНапишите "/start" для возобновления работы.', reply_markup=kb)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters=filters.TEXT & ~filters.COMMAND, callback=misunderstanding)
    start_handler = CommandHandler(command='start', callback=begining)
    end_handler = CommandHandler(command='cancel', callback=cancellation)

    application.add_handler(text_handler)
    application.add_handler(start_handler)
    application.add_handler(end_handler)

    application.run_polling()


main()
