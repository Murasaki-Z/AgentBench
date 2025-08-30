import asyncio
import os
import discord
from dotenv import load_dotenv

# --- Step 1: Configuration ---
# Load credentials and IDs from a .env file in the same directory.
# This keeps your secret token out of the code.
load_dotenv()
TOKEN = os.getenv("DISCORD_TEST_BOT_TOKEN")
TEST_CHANNEL_ID = int(os.getenv("DISCORD_TEST_CHANNEL_ID"))
BOT_USER_ID = int(os.getenv("DISCORD_TEST_BOT_USER_ID"))

# --- Step 2: Client Initialization ---
# The discord.Client object is our connection to Discord.
# We must specify "intents" which are permissions for our bot.
# `message_content` is required to read the text of messages.
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- Step 3: Signaling ---
# An asyncio.Event is a simple flag that one part of the program can set
# and another part can wait for. This is how we will signal that a
# reply has been received.

# --- Step 4: The "Ready" Event Handler (The Sender) ---
# This function is automatically called by the library exactly once
# when the client has successfully logged in and is ready.
@client.event
async def on_ready():
    print(f"--- Test client logged in as {client.user}. ---")
    
    # Get the channel object where the test will be run.
    channel = client.get_channel(TEST_CHANNEL_ID)
    if not channel:
        print(f"!!! ERROR: Could not find channel with ID {TEST_CHANNEL_ID}. Shutting down.")
        await client.close()
        return

    # Send the test message.
    test_message = "@NoFoodWasteBot What do I need for cheese tacos?"
    print(f"--- Sending message: '{test_message}' ---")
    await channel.send(test_message)

    # Now, we wait. The `reply_received_signal.wait()` call will pause
    # this function indefinitely until another part of the code calls
    # `reply_received_signal.set()`.
    print("--- Message sent. Waiting for a reply... ---")
    # await reply_received_signal.wait()

# --- Step 5: The "Message Received" Event Handler (The Receiver) ---
# This function is automatically called by the library every time a new
# message is posted in any channel the bot has access to.
@client.event
async def on_message(message: discord.Message):
    # Filter 1: Ignore messages outside our designated test channel.
    if message.channel.id != TEST_CHANNEL_ID:
        return

    # Filter 2: Ignore messages that are not from the specific bot we are testing.
    if message.author.id != BOT_USER_ID:
        return
    
    # If the message passes the filters, it's the one we want.
    print(f"--- Reply received from bot! ---")
    print("\n--- BOT'S REPLY ---")
    print(message.content)
    print("-------------------\n")

    # Set the signal to "True". This will un-pause the `on_ready` function.
    # reply_received_signal.set()
    
    # Since our job is done, gracefully close the client connection.
    # This will cause the `client.run()` call to finish.
    # await client.close()

# --- Step 6: The Runner ---
# This is the entry point of the script.
if __name__ == "__main__":
    print("--- Starting simple E2E test. Make sure the main bot is running. ---")
    try:
        # client.run(TOKEN) is a simple, blocking function.
        # It handles starting the client, running the event loop, and waiting
        # until client.close() is called.
        client.run(TOKEN)
        print("--- Test finished and client has shut down successfully. ---")
    except Exception as e:
        print(f"!!! An error occurred: {e}")