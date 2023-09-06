import warnings
from contextvars import ContextVar

import trio
import trio_asyncio
from aioredis import Redis
from quart import render_template, websocket, request
from quart_trio import QuartTrio
from pydantic import BaseModel, Field, ValidationError
from hypercorn.trio import serve
from hypercorn.config import Config as HyperConfig

from exceptions import SmscApiError
from smsc_api_methods import request_smsc
from settings import ENV
from db import Database

app = QuartTrio(__name__)
warnings.filterwarnings(action='ignore', category=trio.TrioDeprecationWarning)

smsc_login: ContextVar[str] = ContextVar('smsc_login')
smsc_password: ContextVar[str] = ContextVar('smsc_password')


class Message(BaseModel):
    text: str = Field(min_length=1, max_length=70)


@app.before_serving
async def create_db_pool():
    redis = Redis(
        host=ENV.REDIS.HOST,
        port=ENV.REDIS.PORT,
        password=ENV.REDIS.PASSWORD.get_secret_value()
    )
    app.db_pool = Database(redis)


@app.after_serving
async def close_db_pool():
    await app.db_pool.redis.close()


@app.route('/')
async def index():
    return await render_template('index.html')


@app.route('/send/',  methods=["POST"])
async def create_message():
    db = app.db_pool
    try:
        form = await request.form
        message = Message(text=form['text'])
        payload = {
            'phones': ENV.EMAILS,
            'mes': message.text,
            'subj': ENV.MESSAGE_SUBJECT,
            'sender': ENV.SENDER,
            'mail': 1,
            'valid': ENV.MESSAGE_LIFE_SPAN,
        }
        response = await request_smsc(
            'POST',
            'send',
            login=smsc_login.get(),
            password=smsc_password.get(),
            payload=payload)
        print(response)
        print(f'SMS с текстом "{message.text}" отправлено')

        await trio_asyncio.aio_as_trio(
            db.add_sms_mailing(response['id'], ENV.EMAILS.split(','), message.text)
        )
        all_message_ids = await trio_asyncio.aio_as_trio(db.list_sms_mailings())
        all_sms_mailings = await trio_asyncio.aio_as_trio(
            db.get_sms_mailings(*all_message_ids)
        )

        ids_with_same_text = []
        for sms_mailing in all_sms_mailings:
            if sms_mailing['text'].lower() == message.text.lower():
                ids_with_same_text.append(sms_mailing['sms_id'])
        print('В БД есть SMS с этими id: ', ids_with_same_text)
    except SmscApiError as err:
        return {"errorMessage": err.args}
    except ValidationError as err:
        return {"errorMessage": f"Ошибка валидации: {str(err.errors())}"}
    else:
        return {}


@app.websocket('/ws')
async def ws():
    for i in range(100):
        await websocket.send_json({
            "msgType": "SMSMailingStatus",
            "SMSMailings": [
                {
                    "timestamp": 1123131392.734,
                    "SMSText": "Сегодня гроза! Будьте осторожны!",
                    "mailingId": "1",
                    "totalSMSAmount": 345,
                    "deliveredSMSAmount": int(345 * (i/100)),
                    "failedSMSAmount": 5,
                },
                {
                    "timestamp": 1323141112.924422,
                    "SMSText": "Новогодняя акция!!! Приходи в магазин и получи скидку!!!",
                    "mailingId": "new-year",
                    "totalSMSAmount": 3993,
                    "deliveredSMSAmount": int(3993 * (i/100)),
                    "failedSMSAmount": 0,
                },
            ]
        })
        await trio.sleep(1)


async def run_server():
    async with trio_asyncio.open_loop():
        config = HyperConfig()
        config.bind = ["127.0.0.1:5000"]
        config.use_reloader = True

        await serve(app, config)


if __name__ == '__main__':
    smsc_login.set(ENV.SMSC_LOGIN)
    smsc_password.set(ENV.SMSC_PASSWORD.get_secret_value())
    trio.run(run_server)
