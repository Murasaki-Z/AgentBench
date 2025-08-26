# projects/mexican_cooking_bot/__main__.py
import asyncio
import discord
from pathlib import Path

# --- Project Imports ---
from . import config
from .agent import graph
from core_lib.discord_connector import DiscordConnector
from core_lib.data_sinks import JSONDataSink

# --- Global Services ---

discord_connector = DiscordConnector(
    token=config.DISCORD_BOT_TOKEN,
    bot_name="NoFoodWasteBot" # The name to listen for in messages
)

log_file_path = Path(__file__).parent / "logs" / "production_log.jsonl"
production_data_sink = JSONDataSink(log_path=log_file_path)
print(f"--- Production logging enabled. Writing to: {log_file_path} ---")

async def handle_discord_message(message: discord.Message):
    """
    This is the core async function that will be called by the DiscordConnector
    whenever a relevant message is received.
    """
    
    print(f"--- Received message from {message.author}: '{message.content}' ---")
    
    # Let the user know the bot is thinking...
    # The 'typing()' context manager shows the "Bot is typing..." indicator in Discord
    async with message.channel.typing():
        try:
            # Prepare the initial state for our agent's graph
            initial_state = {
                "request": message.content,
                "intent": None,
                "ingredients_list": [],
                "store_search_results": [],
                "shopping_list": None,
                "missing_items": [],
                "clarification_question": None,
                "evaluation_grade": None,
            }

            # --- Invoke the Agent ---
            # The .ainvoke() method is the asynchronous version of .invoke()
            final_state = await graph.ainvoke(initial_state)
            
            # --- log the info ---
            log_entry = {
                **final_state, # Unpack all the key-value pairs from the agent's state
                "timestamp_utc": message.created_at.isoformat(),
                "discord_user_id": message.author.id,
                "discord_username": str(message.author),
            }
            production_data_sink.write(log_entry)
            print(f"--- Interaction logged for {message.author} ---")

            # --- Determine the Response ---
            response_message = ""
            if final_state.get("shopping_list"):
                response_message = final_state["shopping_list"]
            elif final_state.get("clarification_question"):
                response_message = final_state["clarification_question"]
            else:
                response_message = "I'm sorry, I encountered an issue and don't have a response."
            
            # Send the final response back to the Discord channel
            await message.channel.send(response_message)
            print(f"--- Sent response to {message.author} ---")

        except Exception as e:
            print(f"--- ERROR processing message: {e} ---")
            await message.channel.send("I'm sorry, I ran into a critical error while processing your request.")


async def main():
    """
    The main entry point for the live bot application.
    """
    print("--- Mexican Cooking Bot (Live Discord Edition) ---")
    
    # 1. Register our message handling function with the connector.
    #    This tells the connector what to DO when a message comes in.
    discord_connector.register_on_message(handle_discord_message)
    
    # 2. Start the connector.
    #    This is a blocking call that will run forever until the process is stopped.
    await discord_connector.run()


if __name__ == "__main__":
    # The standard way to run an asyncio application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Bot shutting down ---")