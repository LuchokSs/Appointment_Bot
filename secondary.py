import requests
from data import SERVER, COMPANY_ID, ACCESS_TOKEN, PASSWORD, USER


def make_kb_list(data, back_button=True, cancel_button=True):
    answer = []
    for i in range(len(data)):
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
    else:
        date = date.split('-')
    return f'{date[2]}-{date[1]}-{date[0]}'


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
    req = requests.post(f'{SERVER}/api/Web/WorkerCells', data=req_dict).json()
    req = req['workers'][0]['schedule'][0]['cells']
    for i in req:
        if i['free']:
            result[0].append(i['time_start'])
            result[1].append(i['time_end'])
    return result


def request_token():
    res = requests.post(url='https://patient.simplex48.ru/token',
                        data=f'grant_type=password&username={USER}&password={PASSWORD}',
                        headers={'Content-type': 'application/x-www-form-urlencoded'}).json()
    global ACCESS_TOKEN
    ACCESS_TOKEN = res['access_token']
    return


def intercept_request(request, data, deep=5):
    if deep == 0:
        return False, None
    req = requests.post(request, data=data, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}).json()
    if req == '-1':
        request_token()
        return intercept_request(request, data, deep=deep - 1)
    else:
        return True, req


def make_record_request(context):
    req_dict = {'MEDORG_ID': COMPANY_ID,
                'DOCT_ID': context.user_data['type'],
                'BRA_ID': context.user_data['polyclinic'],
                'WORK_ID': context.user_data['doctor'],
                'Date': context.user_data['day'],
                'timeInterval': '-'.join(context.user_data['time']),
                'Name': ' '.join(context.user_data['name'][:2]),
                'Phone': context.user_data['phone'],
                'firstName': context.user_data['name'][1],
                'middleName': context.user_data['name'][2],
                'lastName': context.user_data['name'][0],
                'birthday': reformat_date(context.user_data['age'])
                }
    res = intercept_request(request=f'{SERVER}/api/Web/recordTelegram', data=req_dict)
    if res[0]:
        return res[1]
    else:
        return False
