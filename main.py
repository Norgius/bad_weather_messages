from contextvars import ContextVar
from unittest.mock import patch

import asks
import asyncclick as click
from environs import Env

from exceptions import SmscApiError

smsc_login: ContextVar[str] = ContextVar('smsc_login')
smsc_password: ContextVar[str] = ContextVar('smsc_password')

CHARSET = 'utf-8'
HTTP_METHODS = ['GET', 'POST']
API_METHODS = ['send', 'status']


async def request_smsc(
    http_method: str,
    api_method: str,
    *,
    payload: dict = {}
) -> dict:
    if http_method not in HTTP_METHODS or api_method not in API_METHODS:
        raise SmscApiError
    if api_method == 'send' and not payload.get('phones', False):
        raise SmscApiError
    url = f'https://smsc.ru/sys/{api_method}.php'

    basic_payload = {
        'login': smsc_login.get(),
        'psw': smsc_password.get(),
        'charset': CHARSET,
        'fmt': 3
    }
    payload.update(basic_payload)

    if api_method == 'POST':
        response = await asks.request(http_method, url, data=payload)
    else:
        response = await asks.request(http_method, url, params=payload)
    response = response.json()
    if 'error' in response:
        raise SmscApiError
    return response


@click.command()
async def main():
    env = Env()
    env.read_env()

    smsc_login.set(env.str('SMTP_LOGIN'))
    smsc_password.set(env.str('SMTP_PASSWORD'))
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


if __name__ == '__main__':
    main(_anyio_backend='trio')
