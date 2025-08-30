# synthetic_users/e2e_client.py (or your online_client.py)
import discord
import asyncio
from typing import Optional
# from projects.mexican_groceries import config 

class E2EDiscordClient:
    """
    A specialized Discord client for End-to-End (E2E) testing.
    Uses an async context manager for robust login/logout.
    """
    def __init__(self, token: str, test_channel_id: int, bot_user_id: int):
        self.token = token
        self.test_channel_id = test_channel_id
        self.bot_user_id = bot_user_id
        
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        
        self.client = discord.Client(intents=intents)
        self._reply_future: Optional[asyncio.Future] = None

        @self.client.event
        async def on_message(message: discord.Message):
            if message.channel.id != self.test_channel_id:
                return
            
            is_from_bot_under_test = message.author.id == self.bot_user_id

            if is_from_bot_under_test and self._reply_future and not self._reply_future.done():
                self._reply_future.set_result(message.content)

    async def send_and_wait_for_reply(self, message_content: str, timeout: int) -> Optional[str]:
        """
        Connects, sends a message, waits for a specific reply, and disconnects.
        """
        loop = asyncio.get_event_loop()
        self._reply_future = loop.create_future()
        
        try:
            # The 'async with' block handles the entire login/logout lifecycle safely.
            # We wrap the whole thing in a timeout.
            async with asyncio.timeout(timeout):
                # We start the client as a background task
                client_task = loop.create_task(self.client.start(self.token))
                
                # Wait for the client to be ready inside the 'with' block
                await self.client.wait_until_ready()
                
                channel = self.client.get_channel(self.test_channel_id)
                if not channel:
                    raise RuntimeError(f"Could not find channel with ID {self.test_channel_id}")

                # Send the message and wait for the reply
                await channel.send(message_content)
                reply = await self._reply_future
                
                # Once we have the reply, we can gracefully close the client
                await self.client.close()
                await client_task # Ensure the client task is fully finished
                
                return reply

        except asyncio.TimeoutError:
            print(f"--- E2E Client: Timed out after {timeout} seconds waiting for a reply. ---")
            # Ensure the client is closed even on timeout
            if not self.client.is_closed():
                await self.client.close()
            return None
        except Exception as e:
            print(f"--- E2E Client: An unexpected error occurred: {e} ---")
            if not self.client.is_closed():
                await self.client.close()
            return None