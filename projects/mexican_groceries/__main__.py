# projects/mexican_cooking_bot/__main__.py
import asyncio
import discord
from pathlib import Path

# --- Project Imports ---
from . import config
from .agent import graph
from core_lib.discord_connector import DiscordConnector
from core_lib.data_sinks import JSONDataSink

from core_lib.image_generation import get_image_generator
from core_lib.image_generation_base import BaseImageGenerator


# --- Global Services ---

discord_connector = DiscordConnector(
    token=config.DISCORD_BOT_TOKEN,
    bot_name="NoFoodWasteBot" # The name to listen for in messages
)

log_file_path = Path(__file__).parent / "logs" / "production_log.jsonl"
production_data_sink = JSONDataSink(log_path=log_file_path)
print(f"--- Production logging enabled. Writing to: {log_file_path} ---")

image_generator: BaseImageGenerator = get_image_generator(
    provider=config.IMAGE_GENERATION_PROVIDER,
    openai_key=config.OPENAI_API_KEY,
    google_key=config.GOOGLE_API_KEY
)
print(f"--- Image generation provider set to: {config.IMAGE_GENERATION_PROVIDER} ---")


# projects/mexican_cooking_bot/__main__.py

async def handle_discord_message(message: discord.Message):
    """
    Core async function that handles an incoming message, runs the agent,
    and conditionally kicks off concurrent image generation.
    """
    print(f"--- Received message from {message.author}: '{message.content}' ---")
    
    async with message.channel.typing():
        # --- Step 1: Run the main agent graph FIRST ---
        # We need the result of the agent to decide if we should generate an image.
        try:
            initial_state = { "request": message.content }
            final_state = await asyncio.wait_for(graph.ainvoke(initial_state), timeout=60.0)
        except asyncio.TimeoutError:
            print("--- ERROR: Main agent task timed out. ---")
            await message.channel.send("I'm sorry, my main thinking process took too long. Please try again.")
            return

        # --- Step 2: Initialize a placeholder for our background task ---
        image_generation_task = None
        
        # --- Step 3: Conditionally start the image generation task ---
        # Check if the agent successfully identified a dish and is providing a shopping list.
        dish_name = final_state.get("dish_name")
        if dish_name and final_state.get("shopping_list"):
            print(f"--- Dish '{dish_name}' identified. Kicking off background image generation. ---")
            image_prompt_text = (
                f"A photorealistic, beautifully lit, rustic-style photo of a delicious, "
                f"authentic plate of homemade {dish_name}. Focus on the food, make it look appetizing."
            )
            # Use asyncio.create_task to start the image generation in the background
            image_generation_task = asyncio.create_task(
                image_generator.generate_image_async(image_prompt_text)
            )

        # --- Step 4: Immediately send the primary text response ---
        # This logic is now simpler as we already have the final_state.
        response_message = ""
        if final_state.get("shopping_list"):
            response_message = final_state["shopping_list"]
        elif final_state.get("clarification_question"):
            response_message = final_state["clarification_question"]
        else:
            response_message = "I'm sorry, I'm not sure how to respond to that."

        await message.channel.send(response_message)
        print(f"--- Sent primary text response to {message.author} ---")

    # --- Step 5: Log the interaction (outside the 'typing' context) ---
    # This logic remains the same.
    log_entry = {
        **final_state,
        "timestamp_utc": message.created_at.isoformat(),
        "discord_user_id": message.author.id,
        "discord_username": str(message.author),
    }
    production_data_sink.write(log_entry)
    print(f"--- Interaction logged for {message.author} ---")

    # --- Step 6: Now, await the background image task, if it exists ---
    if image_generation_task:
        print("--- Waiting for background image generation to complete... ---")
        try:
            # We still await the task we created earlier.
            image_bytes_io = await asyncio.wait_for(image_generation_task, timeout=60.0)
            
            if image_bytes_io and image_bytes_io.getbuffer().nbytes > 0:
                image_bytes_io.seek(0)
                discord_file = discord.File(image_bytes_io, filename="dish_inspiration.png")
                
                await message.channel.send(
                    f"And here's some inspiration for your {dish_name}!",
                    file=discord_file
                )
                print("--- Sent secondary image response. ---")
            else:
                print("--- Image generation completed but produced no data. Skipping image response. ---")
        except asyncio.TimeoutError:
            print("--- ERROR: Image generation task timed out. ---")
        except Exception as e:
            print(f"--- ERROR during image handling: {e} ---")

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