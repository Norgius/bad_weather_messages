import aioredis
import argparse
import trio
import trio_asyncio

from db import Database


def create_argparser():
    parser = argparse.ArgumentParser(description='Redis database usage example')
    parser.add_argument(
        '--host',
        action='store',
        dest='redis_host',
        default='redis://localhost'
    )
    parser.add_argument(
        '--port',
        action='store',
        type=int,
        dest='redis_port',
        default=6379,
    )
    parser.add_argument(
        '--password',
        action='store',
        dest='redis_password',
    )
    return parser


async def main():
    parser = create_argparser()
    args = parser.parse_args()

    async with trio_asyncio.open_loop():
        redis = aioredis.Redis(
            host=args.redis_host,
            port=args.redis_port,
            password=args.redis_password
        )

        try:
            db = Database(redis)

            sms_id = '1'

            phones = [
                '+7 999 519 05 57',
                '911',
                '112',
            ]
            text = 'Вечером будет шторм!'

            await trio_asyncio.aio_as_trio(db.add_sms_mailing(sms_id, phones, text))

            sms_ids = await trio_asyncio.aio_as_trio(db.list_sms_mailings())
            print('Registered mailings ids', sms_ids)

            pending_sms_list = await trio_asyncio.aio_as_trio(db.get_pending_sms_list())
            print('pending:')
            print(pending_sms_list)

            await trio_asyncio.aio_as_trio(db.update_sms_status_in_bulk([
                # [sms_id, phone_number, status]
                [sms_id, '112', 'failed'],
                [sms_id, '911', 'pending'],
                [sms_id, '+7 999 519 05 57', 'delivered'],
                # following statuses are available: failed, pending, delivered
            ]))

            pending_sms_list = await trio_asyncio.aio_as_trio(db.get_pending_sms_list())
            print('pending:')
            print(pending_sms_list)

            sms_mailings = await trio_asyncio.aio_as_trio(db.get_sms_mailings('1'))
            print('sms_mailings')
            print(sms_mailings)

            async def send():
                while True:
                    await trio.sleep(1)
                    await trio_asyncio.aio_as_trio(redis.publish('updates', sms_id))

            async def listen():
                channel = redis.pubsub()
                await trio_asyncio.aio_as_trio(channel.subscribe('updates'))

                while True:
                    message = await trio_asyncio.aio_as_trio(
                        channel.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    )

                    if not message:
                        continue

                    print('Got message:', repr(message['data'].decode()))

            async with trio.open_nursery() as nursery:
                nursery.start_soon(send)
                nursery.start_soon(listen)

        finally:
            redis.close()


if __name__ == '__main__':
    trio.run(main)
