import logging

from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ConversationHandler

from data import BOT_TOKEN, COMPANY_NAME, DOCTORS, POLYCLINICS, TIME, DAY, TYPES


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


tps = ReplyKeyboardMarkup(make_kb_list(TYPES), one_time_keyboard=True, resize_keyboard=True)


async def misunderstanding(update, context):
    await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.', reply_markup=kb)


async def begining(update, context):
    await update.message.reply_html(f"""\tЗдравствуйте! Я - бот для записи на прием в компании {COMPANY_NAME}
    \nВыберите нужого вам врача.""", reply_markup=tps)
    return 0


async def cancellation(update, context):
    await update.message.reply_text('До скорой встречи! \nНапишите "/start" для возобновления работы.', reply_markup=kb)
    context.user_data.clear()
    return ConversationHandler.END


async def choose_polyclinic(update, context):
    type = update.message.text
    if type in TYPES:

        context.user_data['type'] = type
        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS), one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"В какой поликлинике вам нужен {context.user_data['type'].lower()}?", reply_markup=plclnc)
        return 1
    else:
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=tps)
        return 0


async def choose_doctor(update, context):
    polyclinic = update.message.text
    if polyclinic in POLYCLINICS:

        context.user_data['polyclinic'] = polyclinic
        dctr = ReplyKeyboardMarkup(make_kb_list(DOCTORS[polyclinic]), one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"Какой {context.user_data['type'].lower()} вам нужен в поликлинике №{polyclinic}?", reply_markup=dctr)
        return 2
    else:
        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=plclnc)
        return 1


async def choose_day(update, context):
    doctor = update.message.text
    if doctor in DOCTORS[context.user_data['polyclinic']]:
        context.user_data['doctor'] = doctor
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"На какой день вы хотите записаться к {context.user_data['type'].lower()} {context.user_data['doctor']}?",
            reply_markup=days)
        return 3
    else:
        dctr = ReplyKeyboardMarkup(make_kb_list(DOCTORS[context.user_data['polyclinic']]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=dctr)
        return 2


async def choose_time(update, context):
    day = update.message.text
    if day in DAY:
        context.user_data['day'] = day
        times = ReplyKeyboardMarkup(make_kb_list(TIME), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"На какое время вы хотите записаться к {context.user_data['type'].lower()} {context.user_data['doctor']} "
            f"{context.user_data['day']}?", reply_markup=times)
        return 4
    else:
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=days)
        return 3


async def take_name(update, context):
    time = update.message.text
    if time in TIME:
        context.user_data['time'] = time
        await update.message.reply_text(
            f"Для того, чтобы записаться в {context.user_data['polyclinic']} поликлинику к "
            f"{context.user_data['type'].lower()} {context.user_data['doctor']} на "
            f"{context.user_data['day']} в {context.user_data['time']} нам нужно узнать ваше ФИО в формате:"
            f" \nФамилия Имя Отчество")
        return 5
    else:
        times = ReplyKeyboardMarkup(make_kb_list(TIME), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=times)
        return 4


async def take_age(update, context):
    name = update.message.text
    context.user_data['name'] = name
    await update.message.reply_text(f'Теперь на нужно узнать ваш возраст, {name}. \nВ формате: ДД.ММ.ГГГГ')
    return 6


async def take_phone_number(update, context):
    age = update.message.text
    context.user_data['age'] = age
    await update.message.reply_text(f'Укажите пожалуйста ваш номер телефона, {context.user_data["name"]}')
    return 7


async def end_of_dialog(update, context):
    phone_number = update.message.text
    context.user_data['phone_number'] = phone_number
    await update.message.reply_text(f'Вы записаны на {context.user_data["day"]}. Не опаздывайте, хорошего дня!')
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, misunderstanding)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', begining)],

        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_polyclinic)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_doctor)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_day)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_time)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_name)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_age)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_phone_number)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_of_dialog)]
        },

        fallbacks=[CommandHandler('cancel', cancellation)]
    )

    application.add_handler(conv_handler)
    application.add_handler(text_handler)

    application.run_polling()


main()
