import re

import asks
import trio
import asyncclick as click
from environs import Env


ID_MESSAGE_PATTERN = '[\d]{9}'


async def get_status_message(smtp_login, smtp_password, emails, message_id):
    url = 'https://smsc.ru/sys/status.php'
    params = {
        'login': smtp_login,
        'psw': smtp_password,
        'phone': emails,
        'id': message_id,
        'fmt': 3,
    }
    response = await asks.get(url, params=params)
    print(response.json())


@click.command()
async def main():
    env = Env()
    env.read_env()
    url = 'https://smsc.ru/sys/send.php'

    smtp_login = env.str('SMTP_LOGIN')
    smtp_password  = env.str('SMTP_PASSWORD')
    emails = env.list('EMAILS')
    sender = env.str('SENDER')
    message_subject = env.str('MESSAGE_SUBJECT', 'Погода')
    message_life_span = env.int('MESSAGE_LIFE_SPAN', 1)
    text_message = env.str('MESSAGE_TEXT', 'Сегодня будет гроза.')

    emails = ';'.join(emails)
    params = {
        'login': smtp_login,
        'psw': smtp_password,
        'phones': emails,
        'mes': text_message,
        'subj': message_subject,
        'sender': sender,
        'mail': 1,
        'valid': message_life_span,
    }

    response = await asks.get(url, params=params)
    print(response.text)
    message_id = re.search(ID_MESSAGE_PATTERN, response.text)
    if message_id:
        message_id = message_id.group(0)
        await get_status_message(smtp_login, smtp_password, emails, message_id)


if __name__ == '__main__':
    main(_anyio_backend='trio')
