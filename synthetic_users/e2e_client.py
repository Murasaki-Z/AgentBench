# synthetic_users/e2e_client.py
import discord
import asyncio
from typing import Optional

class E2EDiscordClient:
    """
    A specialized Discord client for End-to-End (E2E) testing.
    It connects, sends a single message, and waits for a single reply.
    """
    def __init__(self, token: str, test_channel_id: int):
        self.token = token
        self.test_channel_id = test_channel_id
        
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        
        self.client = discord.Client(intents=intents)
        self._reply_future: Optional[asyncio.Future] = None

        @self.client.event
        async def on_message(message: discord.Message):
            # We only care about messages in our specific test channel
            if message.channel.id != self.test_channel_id:
                return
            
            # Ignore messages sent by this client itself
            if message.author == self.client.user:
                return

            # If the future is waiting, this must be the reply we're looking for.
            if self._reply_future and not self._reply_future.done():
                self._reply_future.set_result(message.content)

    async def send_and_wait_for_reply(self, message_content: str, timeout: int) -> Optional[str]:
        """
        Sends a message to the test channel and waits for a reply.

        Returns the content of the reply message, or None if a timeout occurs.
        """
        try:
            # The asyncio.Task is needed to run the client and our logic concurrently
            await asyncio.wait_for(self._run_test(message_content), timeout=timeout)
            return self._reply_future.result() if self._reply_future else None
        except asyncio.TimeoutError:
            print(f"--- E2E Client: Timed out after {timeout} seconds waiting for a reply. ---")
            return None
        finally:
            if self.client.is_ready():
                await self.client.close()

    async def _run_test(self, message_content: str):
        async def runner():
            # This inner function connects the client. 'start' is blocking.
            await self.client.start(self.token)

        # Start the client in the background
        loop = asyncio.get_event_loop()
        client_task = loop.create_task(runner())

        # Wait until the client is connected and ready
        await self.client.wait_until_ready()
        
        # Get the channel object
        channel = self.client.get_channel(self.test_channel_id)
        if not channel:
            print(f"--- E2E Client: ERROR: Could not find channel with ID {self.test_channel_id} ---")
            return

        # Prepare the Future to receive the result from on_message
        self._reply_future = loop.create_future()
        
        # Send the test message
        await channel.send(message_content)

        # Wait for the on_message event to set the result of the future
        await self._reply_future

        # Once we have the reply, we can stop the client
        await self.client.close()

        # Wait for the client task to finish its shutdown
        await client_task