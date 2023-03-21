import logging
from telegram.ext import Application, MessageHandler, CommandHandler, filters

from data import BOT_TOKEN


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def misunderstanding(update, context):
    await update.message.reply_text('Что-то я не разобрался... Напишите "/start" для начала работы.')


async def begining(update, context):
    await update.message.reply_html("Текст", parse_mode='HTML')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters=filters.TEXT & ~filters.COMMAND, callback=misunderstanding)
    start_handler = CommandHandler(command='start', callback=begining)

    application.add_handler(text_handler)
    application.add_handler(start_handler)

    application.run_polling()


main()
