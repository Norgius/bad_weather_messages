from unittest.mock import patch

import asks
from environs import Env

from exceptions import SmscApiError

CHARSET = 'utf-8'


async def request_smsc(
    http_method: str,
    api_method: str,
    *,
    login: str,
    password: str,
    payload: dict = {}
) -> dict:
    url = f'https://smsc.ru/sys/{api_method}.php'

    basic_payload = {
        'login': login,
        'psw': password,
        'charset': CHARSET,
        'fmt': 3
    }
    payload.update(basic_payload)
    if api_method == 'POST':
        response = await asks.request(http_method, url, data=payload)
    else:
        response = await asks.request(http_method, url, params=payload)

    if response.reason_phrase != 'OK':
        raise SmscApiError(f'Получен код ошибки: "{response.status_code} {response.text}"')
    response = response.json()
    if 'error' in response:
        raise SmscApiError(f'Получена ошибка от api SMSC.ru: "{response["error"]}"')
    return response


async def main():
    env = Env()
    env.read_env()

    emails = env.list('EMAILS')
    sender = env.str('SENDER')
    message_subject = env.str('MESSAGE_SUBJECT', 'Погода')
    message_life_span = env.int('MESSAGE_LIFE_SPAN', 1)
    text_message = env.str('MESSAGE_TEXT', 'Сегодня будет гроза.')

    payload = {
        'phones': ','.join(emails),
        'mes': text_message,
        'subj': message_subject,
        'sender': sender,
        'mail': 1,
        'valid': message_life_span,
    }
    try:
        with patch('__main__.request_smsc') as mock_request_smsc:
            mock_request_smsc.return_value = {'id': 104160267, 'cnt': 1}
            response = await request_smsc('POST', 'send', payload=payload)
        print(response)
        message_id = f'{response.get("id")},' * response.get("cnt")
        payload = {
            'phone': ','.join(emails),
            'id': message_id,
        }

        with patch('__main__.request_smsc') as mock_request_smsc:
            mock_request_smsc.return_value = {
                'status': 0,
                'last_date': '01.09.2023 14:39:01',
                'last_timestamp': 1693568341,
                'flag': 40
            }
            response = await request_smsc('GET', 'status', payload=payload)
        print(response)

    except SmscApiError:
        print('Возникла ошибка')
