import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters

from data import BOT_TOKEN, COMPANY_NAME


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


kb_syms = [['/start']]
kb = ReplyKeyboardMarkup(kb_syms, one_time_keyboard=True)


async def misunderstanding(update, context):
    await update.message.reply_text('Что-то я не разобрался... Напишите "/start" для начала работы.', reply_markup=kb)


async def begining(update, context):
    await update.message.reply_html(f"""\tЗдравствуйте! Я - бот для записи на прием в компании {COMPANY_NAME}
    Выберите один из вариантов, предоставленных ниже.""")


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters=filters.TEXT & ~filters.COMMAND, callback=misunderstanding)
    start_handler = CommandHandler(command='start', callback=begining)

    application.add_handler(text_handler)
    application.add_handler(start_handler)

    application.run_polling()


main()
