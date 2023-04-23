import datetime
import logging

import requests
import telegram
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ConversationHandler

from data import BOT_TOKEN, CELL_NUMBER_LIMIT, IS_CONVERSATION, COVERSATION_TIMEOUT
from data import COMPANY_NAME, COMPANY_ID, DOCTORS, DAY, TYPES, TIME, POLYCLINICS, SERVER, INTERVAL, BEGINNING, FLAGS

from answers import *

from secondary import reformat_date, make_cell_request, make_kb_list, make_record_request, request_token, \
    authorized_request, check_request

DEEP = 1

logging.basicConfig(
    filename='logs.txt',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)
logger = logging.getLogger(__name__)

kb_syms = [['/start']]
deny_syms = [['/cancel', 'Назад']]
kb = ReplyKeyboardMarkup(kb_syms, one_time_keyboard=True, resize_keyboard=True)
deny_kb = ReplyKeyboardMarkup(deny_syms, one_time_keyboard=True, resize_keyboard=True)
reminder_kb = ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True, resize_keyboard=True)
middlename_kb = ReplyKeyboardMarkup([['Нет отчества.'], ['/cancel', 'Назад']],
                                    one_time_keyboard=True,
                                    resize_keyboard=True)

request_token()


async def misunderstanding(update, context):
    answer = update.message.text
    id = update.message.from_user.id
    if id in FLAGS.keys():
        if answer == 'Да' or answer == 'Нет':
            if answer == 'Да':
                if authorized_request(request=f'{SERVER}/api/reception/SetInternetRecordConfirmationState/',
                                      data={'medorgId': COMPANY_ID,
                                            'internetEntryGUID': FLAGS[id]['internetEntryGUID'],
                                            'confirmationState': 11},
                                      request_type='post',
                                      response_type='str'):
                    await update.message.reply_text(f'Ждем Вас завтра по адресу {FLAGS[id]["branchAddress"]}!',
                                                    reply_markup=kb)
            elif answer == 'Нет':
                if authorized_request(request=f'{SERVER}/api/reception/SetInternetRecordConfirmationState/',
                                      data={'medorgId': COMPANY_ID,
                                            'internetEntryGUID': FLAGS[id]['internetEntryGUID'],
                                            'confirmationState': 12},
                                      request_type='post',
                                      response_type='str'):
                    await update.message.reply_text('Запись отменена.',
                                                    reply_markup=kb)
            else:
                await update.message.reply_text(server_problems_answer, reply_markup=kb)
        else:
            global DEEP
            if DEEP > 0:
                await update.message.reply_text('Я не понял Ваш ответ. Выберите один из предложенных на панели.',
                                                reply_markup=reminder_kb)
                DEEP -= 1
            elif DEEP == 0:
                await update.message.reply_text('Я не понял Ваш ответ. Наш диспетчер свяжется с '
                                                'Вами для уточнения информации.',
                                                reply_markup=kb)

        return

    if 'спасибо' in answer.lower():
        await update.message.reply_text('Всегда пожалуйста!', reply_markup=kb)
    else:
        await update.message.reply_text('Что-то я не разобрался... \nНапишите "/start" для начала работы.',
                                        reply_markup=kb)


async def beginning(update, context):
    context.user_data.clear()
    req = requests.get(f'{SERVER}/api/Web/allspec/{COMPANY_ID}').json()

    global TYPES
    TYPES = [[], []]
    for i in req:
        TYPES[0].append(i['id'])
        TYPES[1].append(i['name'])
    types_kb = ReplyKeyboardMarkup(make_kb_list(TYPES[1], back_button=False), one_time_keyboard=True,
                                   resize_keyboard=True)

    await update.message.reply_html(speciality_question, reply_markup=types_kb)
    return 0


async def cancellation(update, context):
    await update.message.reply_text('До скорой встречи! \nНапишите "/start" для возобновления работы.', reply_markup=kb)
    context.user_data.clear()
    global IS_CONVERSATION
    IS_CONVERSATION.pop(update.message.from_user.id, None)
    return ConversationHandler.END


async def choose_polyclinic(update, context):  # 0
    global IS_CONVERSATION
    IS_CONVERSATION[update.message.from_user.id] = True

    type = update.message.text
    if type in TYPES[1]:
        if context.user_data.get('type') is None:
            context.user_data['type'] = TYPES[0][TYPES[1].index(type)]

        global POLYCLINICS
        POLYCLINICS = [[], []]

        req = requests.get(
            f'{SERVER}/api/Web/clinic/{COMPANY_ID}/{context.user_data["type"]}')
        if not check_request(req):
            await update.message.reply_text(server_problems_answer)
            return ConversationHandler.END
        req = req.json()
        if len(req) == 0:
            await update.message.reply_text(
                'Извините, на данный момент данная специальность недоступна ни в одной поликлинике.'
                '\nНапишите "/start" для возобновления работы.', reply_markup=kb)
            return ConversationHandler.END

        for i in req:
            POLYCLINICS[0].append(i['id'])
            POLYCLINICS[1].append(i['name'])

        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS[1]), one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(polyclinic_question, reply_markup=plclnc)
        return 1
    else:
        types_kb = ReplyKeyboardMarkup(make_kb_list(TYPES[1], back_button=False), one_time_keyboard=True,
                                       resize_keyboard=True)
        await update.message.reply_text(missing_data_answer, reply_markup=types_kb)
        return 0


async def choose_doctor(update, context):  # 1
    polyclinic = update.message.text

    if update.message.text == 'Назад':
        types_kb = ReplyKeyboardMarkup(make_kb_list(TYPES[1], back_button=False), one_time_keyboard=True,
                                       resize_keyboard=True)
        await update.message.reply_html(speciality_question, reply_markup=types_kb)
        del context.user_data['type']
        return 0

    if polyclinic in POLYCLINICS[1]:
        if context.user_data.get('polyclinic') is None:
            context.user_data['polyclinic'] = POLYCLINICS[0][POLYCLINICS[1].index(polyclinic)]

        req = requests.get(
            f'{SERVER}/api/Web/allmedicdesc/{COMPANY_ID}/{context.user_data["polyclinic"]}/'
            f'{context.user_data["type"]}')
        if not check_request(req):
            await update.message.reply_text(server_problems_answer)
            return ConversationHandler.END
        req = req.json()

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

        await update.message.reply_text(doctor_question, reply_markup=doctor)
        return 2
    else:
        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS[1]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(missing_data_answer, reply_markup=plclnc)
        return 1


async def choose_day(update, context):  # 2
    doctor = update.message.text

    if update.message.text == 'Назад':
        plclnc = ReplyKeyboardMarkup(make_kb_list(POLYCLINICS[1]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(polyclinic_question, reply_markup=plclnc)
        del context.user_data['polyclinic']
        return 1

    if doctor in DOCTORS[1]:
        if context.user_data.get('doctor') is None:
            context.user_data['doctor'] = DOCTORS[0][DOCTORS[1].index(doctor)]

        req_text = f'{SERVER}/api/Web/freedaysmedic/{COMPANY_ID}' \
                   f'/{context.user_data["type"]}/{context.user_data["polyclinic"]}/{context.user_data["doctor"]}'

        req = requests.get(req_text)
        if not check_request(req):
            await update.message.reply_text(server_problems_answer)
            return ConversationHandler.END
        req = req.json()

        if len(req) == 0:
            await update.message.reply_text(
                'Извините, на данный момент нет доступных дней для записи к выбранному врачу.'
                '\nНапишите "/start" для возобновления работы.', reply_markup=kb)
            return ConversationHandler.END

        global DAY
        DAY = []
        for i in req:
            DAY.append(reformat_date(i['FreeDay'].split('T')[0]))
        days = ReplyKeyboardMarkup(make_kb_list(DAY, limit=CELL_NUMBER_LIMIT),
                                   one_time_keyboard=True,
                                   resize_keyboard=True)

        await update.message.reply_text(record_day_question, reply_markup=days)
        return 3
    else:
        dctr = ReplyKeyboardMarkup(make_kb_list(DOCTORS[1]), one_time_keyboard=True,
                                   resize_keyboard=True)
        await update.message.reply_text(missing_data_answer, reply_markup=dctr)
        return 2


async def choose_time(update, context):  # 3
    day = update.message.text

    if update.message.text == 'Назад':
        doctor = ReplyKeyboardMarkup(make_kb_list(DOCTORS[1]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(doctor_question, reply_markup=doctor)
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
        if not TIME:
            await update.message.reply_text(server_problems_answer)
            return ConversationHandler.END
        if len(TIME[0]) == 0:
            await update.message.reply_text(
                'Извините, на данный момент нет доступных ячеек для записи на выбранный день.'
                '\nНапишите "/start" для возобновления работы.', reply_markup=kb)
            return ConversationHandler.END

        times = ReplyKeyboardMarkup(make_kb_list(TIME[0]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(record_time_question, reply_markup=times)
        return 4
    else:
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(missing_data_answer, reply_markup=days)
        return 3


async def take_surname(update, context):  # 4
    time = update.message.text

    if update.message.text == 'Назад':
        days = ReplyKeyboardMarkup(make_kb_list(DAY), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(record_day_question, reply_markup=days)
        del context.user_data['day']
        return 3

    if time in TIME[0]:
        if context.user_data.get('time') is None:
            context.user_data['time'] = [time, TIME[1][TIME[0].index(time)]]
        await update.message.reply_text(lastname_question, reply_markup=deny_kb)
        return 5
    else:
        times = ReplyKeyboardMarkup(make_kb_list(TIME[0]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(missing_data_answer, reply_markup=times)
        return 4


async def take_name(update, context):  # 5
    name = update.message.text

    if update.message.text == 'Назад':
        times = ReplyKeyboardMarkup(make_kb_list(TIME[0]), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(record_time_question, reply_markup=times)
        del context.user_data['time']
        return 4

    if context.user_data.get('name') is None:
        context.user_data['name'] = [name.capitalize()]
    await update.message.reply_text(firstname_question, reply_markup=deny_kb)
    return 6


async def take_lastname(update, context):  # 6
    name = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(lastname_question, reply_markup=deny_kb)
        del context.user_data['name']
        return 5

    if context.user_data.get('name') is not None and len(context.user_data.get('name')) == 1:
        context.user_data['name'].append(name.capitalize())
    await update.message.reply_text(middlename_question, reply_markup=middlename_kb)
    return 7


async def take_age(update, context):  # 7
    name = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(firstname_question, reply_markup=deny_kb)
        del context.user_data['name'][-1]
        return 6

    if context.user_data.get('name') is not None and len(context.user_data.get('name')) == 2:
        if name == 'Нет отчества.':
            context.user_data['name'].append('')
        else:
            context.user_data['name'].append(name.capitalize())

    await update.message.reply_text(age_question, reply_markup=deny_kb)
    return 8


async def take_phone_number(update, context):  # 8
    age = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(middlename_question, reply_markup=middlename_kb)
        del context.user_data['type'][-1]
        return 7

    if context.user_data.get('age') is None:
        check = age.split('.')
        if not (len(check[0]) == 2 and len(check[1]) == 2 and len(check[2]) == 4):
            await update.message.reply_text("Кажется, вы ввели что-то не так.")
            return 8
        context.user_data['age'] = age
    await update.message.reply_text(phone_question, reply_markup=deny_kb)
    return 9


async def check_data(update, context):  # 9
    phone = update.message.text

    if update.message.text == 'Назад':
        await update.message.reply_text(age_question, reply_markup=deny_kb)
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
            'name': ' '.join(context.user_data['name'])}
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
        await update.message.reply_text(phone_question, reply_markup=deny_kb)
        del context.user_data['phone']
        return 9
    global IS_CONVERSATION
    if answer == 'Всё верно!':
        req = make_record_request(context, update.message.chat_id)
        confirmation_req = authorized_request(f'{SERVER}/api/Web/confirmationAmoCRM/{COMPANY_ID}/{req}',
                                              data=None,
                                              request_type='get')
        if req and confirmation_req:
            await update.message.reply_text(
                f'Вы записаны на {reformat_date(context.user_data["day"])} на {context.user_data["time"][0]}. '
                f'Не опаздывайте, хорошего дня!'
                f'\nДля возобновления работы нажмите /start на клавиатуре.',
                reply_markup=kb)
        else:
            await update.message.reply_text('Запись не удалась. Пожалуйста, повторите попытку позже.'
                                            f'\nДля возобновления работы нажмите /start на клавиатуре.',
                                            reply_markup=kb)
        IS_CONVERSATION.pop(update.message.from_user.id)
        return ConversationHandler.END
    elif answer == 'Есть ошибки':
        await update.message.reply_text(f'Пожалуйста, заполните Вашу заявку заново.', reply_markup=kb)
        IS_CONVERSATION.pop(update.message.from_user.id)
        return ConversationHandler.END
    else:
        choice = ReplyKeyboardMarkup(make_kb_list(['Всё верно!', 'Есть ошибки']), one_time_keyboard=True,
                                     resize_keyboard=True)
        await update.message.reply_text(missing_data_answer, reply_markup=choice)
        return 10


async def request_reminders(context):
    global FLAGS
    req = authorized_request(request=f'{SERVER}/api/reception/ScheduledReceptionRecords/',
                             data={'medorgId': COMPANY_ID,
                                   'branchId': 0,
                                   'date': str(datetime.date.today() + datetime.timedelta(days=1))},
                             response_type='json')
    for i in req[1]['scheduledReceptionRecords']:
        if not IS_CONVERSATION.get(int(i['seoCode'].split('@')[1]), False):
            text = f'Здравствуйте! Напоминаю о Вашей записи на {reformat_date(i["date"].split("T")[0])} в {i["time"]}' \
                   f' к врачу {i["workerName"]} по специальности {i["doctorName"]}.\nВы придете?'
            await telegram.Bot(token=BOT_TOKEN).send_message(chat_id=int(i['seoCode'].split('@')[1]),
                                                             text=text, reply_markup=reminder_kb)
            FLAGS[int(i['seoCode'].split('@')[1])] = i


async def timeout(update, context):
    IS_CONVERSATION.pop(update.message.from_user.id)
    await update.message.reply_text("Вы превысили время ожидания ответа. Заполнение заявки отменено. "
                                    "Для заполнения новой заявки нажмите /start", reply_markup=kb)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, misunderstanding)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', beginning)],

        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_polyclinic)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_doctor)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_day)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_time)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_surname)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_name)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_lastname)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_age)],
            8: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_phone_number)],
            9: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_data)],
            10: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_of_dialog)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, timeout)],
        },

        fallbacks=[CommandHandler('cancel', cancellation)],
        conversation_timeout=COVERSATION_TIMEOUT,
    )

    application.job_queue.run_repeating(callback=request_reminders, interval=INTERVAL, first=BEGINNING)
    application.add_handler(conv_handler)
    application.add_handler(text_handler)

    application.run_polling()


main()
