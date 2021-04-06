import json

import requests

def getcurl(req):
    command = "curl -X {method} -H {headers} -d '{data}' '{uri}'"
    method = req.method
    uri = req.url   
    data = req.body
    headers = ['"{0}: {1}"'.format(k, v) for k, v in req.headers.items()]
    headers = " -H ".join(headers)
    return command.format(method=method, headers=headers, data=data, uri=uri)

def json_data(**kwargs):
    # if 'token' not in kwargs:
    #     kwargs['token'] = TOKEN
    return json.dumps(kwargs)

def test_server():
    data = {'region_id': '45000000000', 'local_time': '2021.04.01T16:10:00', 'subject': u'Москва'}
    url = 'http://10.77.35.96:9028'
    r = requests.post(url + '/api/v1/delivery_date_times', data=json_data(**data), headers=dict(
      ServerAuthorization='---'
    ))
    print(r, r.text)

    print(getcurl(r.request))


def test_current():
    data = {
      'local_time': '2021.04.01T16:10:00', 
      # 'default_region': u'Агрогородок',
    }
    print(u'requested url:')
    # url = 'https://mobile-test.sberbank-tele.com/v4.2/order/data'
    # url = 'https://mobile.sberbank-tele.com/v4.2/order/data'
    url = 'https://order-sim-api.sberbank-tele.com/v4.2/order/data'
    print(url)
    response = requests.post(url, data=json_data(**data))
    # print(response, response.text)
    data = response.json()
    
    print('ANSWER: ')

    cap = 10
    for k, v in data.items():
        # print(k)
        if isinstance(v, dict):
            v = {kk: v[kk] for kk in list(v.keys())[:cap]}
        elif isinstance(v, list):
            v = v[:cap]
        
        data[k] = v

    # print(v)
    print(json.dumps(data, indent=4,ensure_ascii=False))
    return data

# data = test_current()
data = test_server()
