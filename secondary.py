import datetime

import requests
import telegram

from data import SERVER, COMPANY_ID, ACCESS_TOKEN, PASSWORD, USER


def check_age(age):
    try:
        age = datetime.datetime.strptime(reformat_date(age) + " 00:00:00", '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return False
    except IndexError:
        return False
    if age > datetime.datetime.now():
        return False
    if datetime.datetime.now().year - age.year >= 100:
        return False
    return True


def check_phone(phone):
    if not phone.isdigit():
        return False
    if len(phone) != 10:
        return False
    return phone


def make_kb_list(data, limit=2e32, back_button=True, cancel_button=True):
    answer = []
    for i in range(len(data)):
        if i >= limit:
            break
        if i % 3 == 0:
            answer.append([])
        answer[-1].append(data[i])
    if cancel_button:
        answer.append(['/cancel'])
        if back_button:
            answer[-1].append('Назад')
    elif back_button:
        answer.append(['Назад'])
    return answer


def reformat_date(date):
    if '.' in date:
        date = date.split('.')
        return f'{date[2]}-{date[1]}-{date[0]}'
    else:
        date = date.split('-')
        return f'{date[2]}.{date[1]}.{date[0]}'


def make_cell_request(medorg_id,
                      branch_id,
                      worker_id,
                      doctor_id,
                      date_start,
                      date_end):
    result = [[], []]
    req_dict = {'medorg_id': medorg_id,
                'branch_id': branch_id,
                'worker_id': worker_id,
                'doctor_id': doctor_id,
                'date_start': date_start,
                'date_end': date_end,
                'reception_kind': 0}
    req = requests.post(f'{SERVER}/api/Web/WorkerCells', data=req_dict)
    if not check_request(req):
        return False
    req = req.json()
    req = req['workers'][0]['schedule']
    for g in req:
        for i in g['cells']:
            if i['free']:
                result[0].append(i['time_start'])
                result[1].append(i['time_end'])
    return result


def check_request(request):
    if request.status_code == 200:
        return True
    return False


def request_token():
    res = requests.post(url=f'{SERVER}/token',
                        data=f'grant_type=password&username={USER}&password={PASSWORD}',
                        headers={'Content-type': 'application/x-www-form-urlencoded'}).json()
    global ACCESS_TOKEN
    ACCESS_TOKEN = res['access_token']
    return


def authorized_request(request, data, request_type='post', deep=2, response_type='str'):
    req = []
    if deep == 0:
        return False, None
    if request_type == 'post':
        req = requests.post(request, data=data, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
    elif request_type == 'get':
        req = requests.get(request, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
    if check_request(req) and req.text != "-1" and req.text != "0":
        if response_type == 'str':
            return True, req.text
        if response_type == 'json':
            return True, req.json()
    else:
        request_token()
        return authorized_request(request=request, data=data, deep=deep - 1)


def make_record_request(context, chat_id):
    req_dict = {'MEDORG_ID': COMPANY_ID,
                'DOCT_ID': context.user_data['type'],
                'BRA_ID': context.user_data['polyclinic'],
                'WORK_ID': context.user_data['doctor'],
                'Date': context.user_data['day'],
                'timeInterval': '-'.join(context.user_data['time']),
                'Name': ' '.join(context.user_data['name'][:2]),
                'Phone': context.user_data['phone'],
                'seoCode': f'telegram@{chat_id}',
                'firstName': context.user_data['name'][1],
                'middleName': context.user_data['name'][2],
                'lastName': context.user_data['name'][0],
                'birthday': reformat_date(context.user_data['age'])
                }
    res = authorized_request(request=f'{SERVER}/api/Web/recordTelegram', data=req_dict)
    if res[0]:
        return res[1]
    else:
        return False
