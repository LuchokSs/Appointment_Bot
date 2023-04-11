import logging

import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ConversationHandler

from data import BOT_TOKEN
from data import COMPANY_NAME, COMPANY_ID, DOCTORS, DAY, TYPES, TIME, POLYCLINICS, SERVER

from secondary import reformat_date, make_cell_request, make_kb_list

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

kb_syms = [['/start']]
deny_syms = [['/cancel', 'Назад']]
kb = ReplyKeyboardMarkup(kb_syms, one_time_keyboard=True, resize_keyboard=True)
deny_kb = ReplyKeyboardMarkup(deny_syms, one_time_keyboard=True, resize_keyboard=True)

req = requests.get(f'{SERVER}/api/Web/allspec/{COMPANY_ID}').json()

for i in req:
    TYPES[0].append(i['id'])
    TYPES[1].append(i['name'])
types_kb = ReplyKeyboardMarkup(make_kb_list(TYPES[1], back_button=False), one_time_keyboard=True, resize_keyboard=True)


async def misunderstanding(update, context):
    answer = update.message.text
    if 'спасибо' in answer.lower():
        await update.message.reply_text('Всегда пожалуйста!', reply_markup=kb)
    else:
        await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.',
                                        reply_markup=kb)


async def begining(update, context):
    await update.message.reply_html(f"""\tЗдравствуйте! Я - бот для записи на прием в компании {COMPANY_NAME}
    \nВыберите нужого вам врача.""", reply_markup=types_kb)
    return 0


async def cancellation(update, context):
    await update.message.reply_text('До скорой встречи! \nНапишите "/start" для возобновления работы.', reply_markup=kb)
    context.user_data.clear()
    return ConversationHandler.END


async def choose_polyclinic(update, context):  # 0
    type = update.message.text
    if type in TYPES[1]:
        if context.user_data.get('type') is None:
            context.user_data['type'] = TYPES[0][TYPES[1].index(type)]

        global POLYCLINICS
        POLYCLINICS = [[], []]

        req = requests.get(
            f'{SERVER}/api/Web/clinic/{COMPANY_ID}/{context.user_data["type"]}').json()

        if len(req) == 0:
            await update.message.reply_text(
                'Извините, на данный момент данная специальность недоступна ни в одной поликлинике.'
                '\nНапишите "/start" для возобновления работы.', reply_markup=kb)
            return ConversationHandler.END

        for i in req:
            POLYCLINICS[0].append(i['id'])
            POLYCLINICS[1].append(i['name'])

        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS[1]), one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"В какую поликлинику вы хотите записаться?"
            f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
            f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.", reply_markup=plclnc)
        return 1
    else:
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=types_kb)
        return 0


async def choose_doctor(update, context):  # 1
    polyclinic = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_html(f"""\tЗдравствуйте! Я - бот для записи на прием в компании {COMPANY_NAME}
            \nВыберите нужого вам врача.""", reply_markup=types_kb)
        del context.user_data['type']
        return 0

    if polyclinic in POLYCLINICS[1]:
        if context.user_data.get('polyclinic') is None:
            context.user_data['polyclinic'] = POLYCLINICS[0][POLYCLINICS[1].index(polyclinic)]

        req = requests.get(
            f'{SERVER}/api/Web/allmedicdesc/{COMPANY_ID}/{context.user_data["polyclinic"]}/'
            f'{context.user_data["type"]}').json()

        global DOCTORS
        DOCTORS = [[], []]

        if len(req) == 0:
            await update.message.reply_text(
                'Извините, на данный момент нет врачей данной специальности в выбранной поликлинике.'
                '\nНапишите "/start" для возобновления работы.', reply_markup=kb)
            return ConversationHandler.END

        for i in req:
            DOCTORS[0].append(i['id'])
            DOCTORS[1].append(i['name'])

        doctor = ReplyKeyboardMarkup(make_kb_list(DOCTORS[1]), one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"Выберите врача, к которому желаете пойти."
            f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
            f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.",
            reply_markup=doctor)
        return 2
    else:
        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS[1]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=plclnc)
        return 1


async def choose_day(update, context):  # 2
    doctor = update.message.text

    if update.message.text == 'Назад':
        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS[1]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"В какую поликлинику вы хотите записаться?"
            f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
            f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.", reply_markup=plclnc)
        del context.user_data['polyclinic']
        return 1

    if doctor in DOCTORS[1]:
        if context.user_data.get('doctor') is None:
            context.user_data['doctor'] = DOCTORS[0][DOCTORS[1].index(doctor)]

        req_text = f'{SERVER}/api/Web/freedaysmedic/{COMPANY_ID}' \
                   f'/{context.user_data["type"]}/{context.user_data["polyclinic"]}/{context.user_data["doctor"]}'

        req = requests.get(req_text).json()

        if len(req) == 0:
            await update.message.reply_text(
                'Извините, на данный момент нет доступных дней для записи к выбранному врачу.'
                '\nНапишите "/start" для возобновления работы.', reply_markup=kb)
            return ConversationHandler.END

        global DAY
        DAY = []
        for i in req:
            DAY.append(reformat_date(i['FreeDay'].split('T')[0]))
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"На какой день вы хотите записаться?"
            f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
            f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.",
            reply_markup=days)
        return 3
    else:
        dctr = ReplyKeyboardMarkup(make_kb_list(DOCTORS[1]), one_time_keyboard=True,
                                   resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=dctr)
        return 2


async def choose_time(update, context):  # 3
    day = update.message.text

    if update.message.text == 'Назад':
        doctor = ReplyKeyboardMarkup(make_kb_list(DOCTORS[1]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Выберите врача, к которому желаете пойти."
            f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
            f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.",
            reply_markup=doctor)
        del context.user_data['doctor']
        return 2

    if day in DAY:
        if context.user_data.get('day') is None:
            context.user_data['day'] = reformat_date(day)

        global TIME
        TIME = make_cell_request(COMPANY_ID,
                                 context.user_data['polyclinic'],
                                 context.user_data['doctor'],
                                 context.user_data['type'],
                                 context.user_data['day'],
                                 context.user_data['day'])
        if len(TIME[0]) == 0:
            await update.message.reply_text(
                'Извините, на данный момент нет доступных ячеек для записи на выбранный день.'
                '\nНапишите "/start" для возобновления работы.', reply_markup=kb)
            return ConversationHandler.END

        times = ReplyKeyboardMarkup(make_kb_list(TIME[0]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"На какое время вы хотите записаться?"
                                        f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
                                        f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.",
                                        reply_markup=times)
        return 4
    else:
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=days)
        return 3


async def take_name(update, context):  # 4
    time = update.message.text

    if update.message.text == 'Назад':
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"На какой день вы хотите записаться?"
            f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
            f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.",
            reply_markup=days)
        del context.user_data['day']
        return 3

    if time in TIME[0]:
        if context.user_data.get('time') is None:
            context.user_data['time'] = [time, TIME[1][TIME[0].index(time)]]
        await update.message.reply_text(
            f"Для того, чтобы записаться в нам нужно узнать Ваше ФИО."
            f" \nВведите Вашу фамилию с прописной буквы.", reply_markup=deny_kb)
        return 5
    else:
        times = ReplyKeyboardMarkup(make_kb_list(TIME[0]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=times)
        return 4


async def take_surname(update, context):  # 5
    name = update.message.text

    if update.message.text == 'Назад':
        times = ReplyKeyboardMarkup(make_kb_list(TIME[0]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"На какое время вы хотите записаться?"
                                        f"\nДля отмены напишите /cancel или нажмите на клавиатуре."
                                        f"\nЧтобы вернутся назад, введите Назад или нажмите на клавиатуре.",
                                        reply_markup=times)
        del context.user_data['time']
        return 4

    if context.user_data.get('name') is None:
        context.user_data['name'] = [name]
    await update.message.reply_text(
        f" Введите Ваше имя с прописной буквы.", reply_markup=deny_kb)
    return 6


async def take_lastname(update, context):  # 6
    name = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(
            f"Для того, чтобы записаться в нам нужно узнать Ваше ФИО."
            f" \nВведите Вашу фамилию с прописной буквы.", reply_markup=deny_kb)
        del context.user_data['name']
        return 5

    if context.user_data.get('name') is not None and len(context.user_data.get('name')) == 1:
        context.user_data['name'].append(name)
    await update.message.reply_text(
        f" Введите Ваше отчество с прописной буквы.", reply_markup=deny_kb)
    return 7


async def take_age(update, context):  # 7
    name = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(
            f" Введите Ваше имя с прописной буквы.", reply_markup=deny_kb)
        del context.user_data['name'][-1]
        return 6

    if context.user_data.get('name') is not None and len(context.user_data.get('name')) == 2:
        context.user_data['name'].append(name)

    context.user_data['name'] = ' '.join(context.user_data['name'])

    await update.message.reply_text(
        f'Пожалуйста, укажите дату рождения в формате ДД.ММ.ГГГГ', reply_markup=deny_kb)
    return 8


async def take_phone_number(update, context):  # 8
    age = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(
            f" Введите Ваше отчество с прописной буквы.", reply_markup=deny_kb)
        del context.user_data['type'][-1]
        return 7

    if context.user_data.get('age') is None:
        check = age.split('.')
        if not (len(check[0]) == 2 and len(check[1]) == 2 and len(check[2]) == 4):
            await update.message.reply_text("Кажется, вы ввели что-то не так.")
            return 8
        context.user_data['age'] = age
    await update.message.reply_text(f'Пожалуйста, укажите ваш номер телефона.', reply_markup=deny_kb)
    return 9


async def check_data(update, context):  # 9
    phone = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(
            f'Пожалуйста, укажите дату рождения в формате ДД.ММ.ГГГГ', reply_markup=deny_kb)
        del context.user_data['age']
        return 8

    if context.user_data.get('phone') is None:
        context.user_data['phone'] = phone
    choice = ReplyKeyboardMarkup(make_kb_list(['Всё верно!', 'Есть ошибки']), one_time_keyboard=True,
                                 resize_keyboard=True)
    await update.message.reply_text(
        f'Пожалуйста, проверьте кооректность введенных данных.\nДля отмены напишите /cancel.')
    data = {'polyclinic': POLYCLINICS[1][POLYCLINICS[0].index(context.user_data['polyclinic'])],
            'type': TYPES[1][TYPES[0].index(context.user_data['type'])],
            'doctor': DOCTORS[1][DOCTORS[0].index(context.user_data['doctor'])],
            'day': reformat_date(context.user_data['day']),
            'time': context.user_data['time'][0],
            'phone': context.user_data['phone'],
            'age': context.user_data['age'],
            'name': context.user_data['name']}
    await update.message.reply_text(
        f"Вы записываетесь в {data['polyclinic']} по специальности "
        f"{data['type'].lower()} к врачу {data['doctor']} на "
        f"{data['day']} в {data['time']}.\n"
        f"Ваш номер телефона: {data['phone']}\n"
        f"Дата вашего рождения: {data['age']}\n"
        f"Ваше ФИО: {data['name']}")
    await update.message.reply_text(f"Всё верно?", reply_markup=choice)
    return 10


async def end_of_dialog(update, context):  # 10
    answer = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(f'Пожалуйста, укажите ваш номер телефона.', reply_markup=deny_kb)
        del context.user_data['phone']
        return 9

    if answer == 'Всё верно!':
        await update.message.reply_text(f'Вы записаны на {context.user_data["day"]}. Не опаздывайте, хорошего дня!'
                                        f'\nДля возобновления работы напишите /start или нажмите /start на клавиатуре.',
                                        reply_markup=kb)
        return ConversationHandler.END
    elif answer == 'Есть ошибки':
        await update.message.reply_text(f'Пожалуйста, заполните вашу заявку заново.', reply_markup=kb)
        return ConversationHandler.END
    else:
        choice = ReplyKeyboardMarkup(make_kb_list(['Всё верно!', 'Есть ошибки']), one_time_keyboard=True,
                                     resize_keyboard=True)
        await update.message.reply_text('Такого нет в моих данных... \nНапишите ваш ответ еще раз.',
                                        reply_markup=choice)
        return 10


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
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_surname)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_lastname)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_age)],
            8: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_phone_number)],
            9: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_data)],
            10: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_of_dialog)]
        },

        fallbacks=[CommandHandler('cancel', cancellation)]
    )

    application.add_handler(conv_handler)
    application.add_handler(text_handler)

    application.run_polling()


main()
