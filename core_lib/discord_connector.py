# core_library/discord_connector.py
import discord
import asyncio
from typing import Callable, Coroutine

# Define a type hint for the async callback function we'll use
AsyncCallback = Callable[[discord.Message], Coroutine]

class DiscordConnector:
    """
    A class to handle the connection and communication with the Discord API.
    """
    def __init__(self, token: str, bot_name: str):
        if not token:
            raise ValueError("Discord token cannot be empty.")
        
        self.token = token
        self.bot_name = bot_name.lower()
        
        # Set up the discord client with the necessary intents
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        
        self.client = discord.Client(intents=intents)
        self._on_message_callback: AsyncCallback | None = None
        
        # --- Event Handlers ---
        @self.client.event
        async def on_ready():
            print(f'--- Discord Connector: Logged in as {self.client.user} ---')

        @self.client.event
        async def on_message(message: discord.Message):
            # Don't let the bot reply to itself
            if message.author == self.client.user:
                return

            # Check if the bot was mentioned or if it's a DM
            is_mentioned = self.client.user in message.mentions
            is_dm = isinstance(message.channel, discord.DMChannel)
            
            # Check if the bot's name is in the message (case-insensitive)
            name_in_message = self.bot_name in message.content.lower()

            if (is_mentioned or is_dm or name_in_message) and self._on_message_callback:
                # Clean the message content by removing the bot's mention/name
                cleaned_content = message.content.replace(f'<@{self.client.user.id}>', '').strip()
                cleaned_content = cleaned_content.replace(self.bot_name, '', 1).strip()
                
                # Create a copy of the message to modify its content
                # This is safer than modifying the original message object
                message_copy = message
                message_copy.content = cleaned_content

                await self._on_message_callback(message_copy)

    def register_on_message(self, callback: AsyncCallback):
        """
        Registers an async function to be called when a relevant message is received.
        """
        self._on_message_callback = callback
        print("--- Discord Connector: Message handler registered. ---")

    async def run(self):
        """
        Starts the Discord client. This is a blocking call.
        """
        try:
            await self.client.start(self.token)
        except discord.errors.LoginFailure:
            print("--- Discord Connector: ERROR: Improper token has been passed. ---")
        except Exception as e:
            print(f"--- Discord Connector: An error occurred: {e} ---")