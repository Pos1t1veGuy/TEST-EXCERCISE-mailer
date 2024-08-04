import json, asyncio, socket
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from asgiref.sync import sync_to_async

from .mailer import Mailer
from .models import EmailAccount, IMAP_server, EmailMessage, EmailAttachment, msg_to_model


class EmailConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)

        match data.get('type'):
            case 'imap-form':
                data = json.loads(text_data)
                email = data.get('email')
                password = data.get('password')
                server = data.get('server')
                port = data.get('port')
                mailbox = data.get('mailbox')
                scan_range = data.get('range')

                await self.scan_mailbox(str(email), str(password), str(server), int(port), str(mailbox), int(scan_range))

    async def scan_mailbox(self, email: str, password: str, server: str, port: int, mailbox: str, scan_range: int):
        try:
            imap = Mailer(email, password, server, port=port)
            imap_mb = imap[mailbox]
        except socket.gaierror:
            await self.send(text_data=json.dumps({
                'type': 'ERROR',
                'message': 'Invalid server or port',
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'ERROR',
                'message': str(e),
            }))

        imap_server, _ = await sync_to_async(IMAP_server.objects.get_or_create)(url=server, port=port)
        user, _ = await sync_to_async(EmailAccount.objects.get_or_create)(email=email, password=password, server=imap_server)

        length = len(imap_mb)
        if scan_range == -1:
            scan_range = length
        else:
            scan_range = min(scan_range, length)

        await self.send(text_data=json.dumps({
            'type': 'scanning_start',
            'from': length - scan_range,
            'to': length,
        }))

        step = 30
        if step <= scan_range:
            tasks = []
            last_i = 1
            for i in range(length - scan_range, length, step):
                tasks.append(self.scan_range(email, password, server, port, mailbox, i, i+step, user))
                last_i = i

            tasks.append(self.scan_range(email, password, server, port, mailbox, last_i+step, length, user))
            await asyncio.gather(*tasks)
        else:
            await self.scan_range(email, password, server, port, mailbox, length - scan_range, length, user)
    
    async def scan_range(self, email: str, password: str, server: str, port: int, mailbox: str, slice_start: int, slice_end: int, user: 'EmailAccount'):
        imap = Mailer(email, password, server, port=port)
        imap_mb = imap[mailbox]

        for msg in imap_mb[slice_start:slice_end]:

            imap_url = await sync_to_async(lambda: user.server.url)()
            if not await sync_to_async(EmailMessage.objects.filter(id=msg.id, sender=user).exists)():
                msg_model = await sync_to_async(msg_to_model)(msg, user)
                await sync_to_async(msg_model.save)()
            else:
                msg_model = await sync_to_async(EmailMessage.objects.get)(id=msg.id, sender=user)

            await self.send(text_data=json.dumps({
                'type': 'scan-progress',
                'message': {
                    **msg.serialize(),
                    'attachments': [
                        {
                            'name': file.name,
                            'url': file.url
                        } for file in await sync_to_async(lambda: list(msg_model.attachments.all()) )()
                    ],
                },
            }))