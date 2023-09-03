from contextvars import ContextVar

from quart import render_template, websocket, request
from quart_trio import QuartTrio
from pydantic import BaseModel, Field, ValidationError

from exceptions import SmscApiError
from smsc_api_methods import request_smsc
from settings import ENV


app = QuartTrio(__name__)

smsc_login: ContextVar[str] = ContextVar('smsc_login')
smsc_password: ContextVar[str] = ContextVar('smsc_password')


class Message(BaseModel):
    text: str = Field(min_length=1, max_length=70)


@app.route('/')
async def index():
    return await render_template('index.html')


@app.route('/send/',  methods=["POST"])
async def create_message():
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
    except SmscApiError as err:
        return {"errorMessage": err.args}
    except ValidationError as err:
        return {"errorMessage": f"Ошибка валидации: {str(err.errors())}"}
    else:
        print(f'SMS с текстом "{message.text}" отправлено')
        return {}


@app.websocket('/ws')
async def ws():
    while True:
        data = await websocket.receive()
        await websocket.send(f"echo {data}")


if __name__ == '__main__':
    smsc_login.set(ENV.SMSC_LOGIN)
    smsc_password.set(ENV.SMSC_PASSWORD.get_secret_value())
    app.run(port=5000)


# @app.websocket('/api/v2/ws')
# @collect_websocket
# async def ws_v2(queue):
#     while True:
#         data = await queue.get()
#         await websocket.send(data)


# connected_websockets = set()

# def collect_websocket(func):
#     @wraps(func)
#     async def wrapper(*args, **kwargs):
#         global connected_websockets
#         queue = asyncio.Queue()
#         connected_websockets.add(queue)
#         try:
#             return await func(queue, *args, **kwargs)
#         finally:
#             connected_websockets.remove(queue)
#     return wrapper

# async def broadcast(message):
#     for queue in connected_websockets:
#         await queue.put(message)
