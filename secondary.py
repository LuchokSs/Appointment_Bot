import requests
from data import SERVER


def make_kb_list(data):
    answer = []
    for i in range(len(data)):
        if i % 3 == 0:
            answer.append([])
        answer[-1].append(data[i])
    answer.append(['/cancel', 'Назад'])
    return answer


def reformat_date(date):
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