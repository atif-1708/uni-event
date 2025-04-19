import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging

class CustomHandler(Debugging):
    def handle_DATA(self, server, session, envelope):
        print('Message from:', envelope.mail_from)
        print('Message for:', envelope.rcpt_tos)
        print('Message data:')
        print(envelope.content.decode('utf8', errors='replace'))
        print('End of message')
        return '250 OK'

async def amain():
    handler = CustomHandler()
    controller = Controller(handler, hostname='localhost', port=1025)
    controller.start()
    print(f"Mail server started at localhost:1025")
    print(f"Press Ctrl+C to stop the server")
    
    # Keep the server running
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(amain())
    except KeyboardInterrupt:
        print("Mail server stopped")