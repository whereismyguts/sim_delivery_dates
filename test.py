import json

import requests
#
# url = 'https://test-podkliuchi.sberbank-tele.com'
#
# r = requests.post(url + '/api/v1/delivery_date_times')
# print(r)

data = {'default_region': '41000000000', 'local_time': '2021.02.14T16:10:00'}

def json_data(**kwargs):
    # if 'token' not in kwargs:
    #     kwargs['token'] = TOKEN
    return json.dumps(kwargs)

print('requested url:')
url = 'https://mobile.sberbank-tele.com/v4.2/order/data'
print(url)
response = requests.post(url, data=json_data(**data))
print(response)



resp_error = {
  "reply": "local_time required in format: \"yyyy.mm.ddTHH:MM:SS\"",
  "result": 0,
  "error": 1
}

resp_no_region = {
  "delivery_dates": {},
  "delivery_times": {},

  "delivery_prices": {
    "57000000000": 300,
    "46000000000": 500,
    "87000000000": 300,
    "66000000000": 300,
  },
  "default_region": "46000000000",
  "result": 1,
  "error": 0,

  "delivery_info_text": {
    "57000000000": "Автоматически подключится выбранный тариф",
    "46000000000": "Автоматически подключится выбранный тариф",
    "87000000000": "Автоматически подключится выбранный тариф",
    "66000000000": "Автоматически подключится выбранный тариф",
    }
}

resp_with_region = {
  "delivery_dates": {
    "default": [
      "30.03.2021",
      "31.03.2021",
      "01.04.2021",
      "02.04.2021",
      "03.04.2021"
    ],
    "20000000000": [
      "30.03.2021",
      "31.03.2021",
      "01.04.2021",
      "02.04.2021",
      "03.04.2021"
    ],
    "20000000000:Воронеж": [
      "30.03.2021",
      "31.03.2021",
      "01.04.2021",
      "02.04.2021",
      "03.04.2021"
    ]
  },
  "delivery_prices": {
    "default": 300,
    "20000000000": 300,
    "20000000000:Воронеж": 300
  },
  "default_region": "20000000000",
  "result": 1,
  "error": 0,
  "delivery_times": {
    "default": [
      "09:00 - 18:00"
    ],
    "31.03.2021": [
      "09:00 - 18:00"
    ],
    "30.03.2021": [
      "09:00 - 18:00"
    ],
    "02.04.2021": [
      "09:00 - 18:00"
    ],
    "03.04.2021": [
      "09:00 - 18:00"
    ],
    "01.04.2021": [
      "09:00 - 18:00"
    ]
  },
  "delivery_info_text": {
    "default": "Автоматически подключится выбранный тариф",
    "20000000000": "Автоматически подключится выбранный тариф"
  },
  "delivery_regions": [
    {
      "id": "20000000000",
      "name": "Воронеж"
    }
  ]
}