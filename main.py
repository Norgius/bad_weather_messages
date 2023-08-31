import asks
import trio
import asyncclick as click
from environs import Env

url = 'https://smsc.ru/sys/send.php'

@click.command()
async def main():
    env = Env()
    env.read_env()

    smtp_login = env.str('SMTP_LOGIN')
    smtp_password  = env.str('SMTP_PASSWORD')
    emails = env.list('EMAILS')
    sender = env.str('SENDER')
    message_subject = env.str('MESSAGE_SUBJECT', 'Погода')
    message_life_span = env.int('MESSAGE_LIFE_SPAN', 1)
    text_message = env.str('MESSAGE_TEXT', 'Сегодня будет гроза.')

    params = {
        'login': smtp_login,
        'psw': smtp_password,
        'phones': ';'.join(emails),
        'mes': text_message,
        'subj': message_subject,
        'sender': sender,
        'mail': 1,
        'valid': message_life_span,
    }
    response = await asks.get(url, params=params)

    print(response.text)


if __name__ == '__main__':
    main(_anyio_backend='trio')
