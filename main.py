import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ConversationHandler

from data import BOT_TOKEN, COMPANY_NAME, DOCTORS, POLYCLINICS, TIME, DAY


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


kb_syms = [['/start']]
kb = ReplyKeyboardMarkup(kb_syms, one_time_keyboard=True, resize_keyboard=True)


def make_kb_list(values):
    values_lst = []
    for i in range(1, len(values) + 1):
        if i % 2 != 0:
            values_lst.append([values[i - 1]])
        else:
            values_lst[-1].append(values[i - 1])
    values_lst.append(['/cancel'])
    return values_lst


plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS), one_time_keyboard=True, resize_keyboard=True)


async def misunderstanding(update, context):
    await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.', reply_markup=kb)


async def begining(update, context):
    await update.message.reply_html(f"""\tЗдравствуйте! Я - бот для записи на прием в компании {COMPANY_NAME}
    \nВыберите нужную вам поликлинику.""", reply_markup=plclnc)
    return 1


async def cancellation(update, context):
    await update.message.reply_text('До скорой встречи! \nНапишите "/start" для возобновления работы.', reply_markup=kb)


async def choose_doctor(update, context):
    polyclinic = update.message.text
    if polyclinic in POLYCLINICS:

        context.user_data['polyclinic'] = polyclinic
        dctr = ReplyKeyboardMarkup(make_kb_list(DOCTORS[polyclinic]), one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"Какой врач вам нужен в поликлинике №{polyclinic}?", reply_markup=dctr)
        return 2
    else:
        context.user_data.clear()
        await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.',
                                        reply_markup=kb)
        return ConversationHandler.END


async def choose_day(update, context):
    doctor = update.message.text
    if doctor in DOCTORS[context.user_data['polyclinic']]:
        context.user_data['doctor'] = doctor
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"На какой день вы хотите записаться к {context.user_data['doctor']}?", reply_markup=days)
        return 3
    else:
        context.user_data.clear()
        await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.',
                                        reply_markup=kb)
        return ConversationHandler.END


async def choose_time(update, context):
    day = update.message.text
    if day in DAY:
        context.user_data['day'] = day
        times = ReplyKeyboardMarkup(make_kb_list(TIME), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"На какое время вы хотите записаться к {context.user_data['doctor']} "
            f"{context.user_data['day']}?", reply_markup=times)
        return 4
    else:
        context.user_data.clear()
        await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.',
                                        reply_markup=kb)
        return ConversationHandler.END


async def end_of_dialog(update, context):
    time = update.message.text
    if time in TIME:
        context.user_data['time'] = time
        await update.message.reply_text(
            f"Вы записаны в {context.user_data['polyclinic']} поликлинику к {context.user_data['doctor']} на "
            f"{context.user_data['day']} в {context.user_data['time']}. Не опаздывайте, хорошего дня!")
        return ConversationHandler.END
    else:
        context.user_data.clear()
        await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.',
                                        reply_markup=kb)
        return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, misunderstanding)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', begining)],

        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_doctor)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_day)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_time)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_of_dialog)]
        },

        fallbacks=[CommandHandler('cancel', cancellation)]
    )

    application.add_handler(conv_handler)
    application.add_handler(text_handler)

    application.run_polling()


main()
