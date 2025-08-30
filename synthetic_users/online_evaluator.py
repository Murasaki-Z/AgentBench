# --- Standard Library Imports ---
import sys
import asyncio
from pathlib import Path

# --- Third-Party Imports ---
import discord
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- Path Hack to allow imports from the project root ---
# This ensures that the script can be run from anywhere and still find project modules.
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# --- Local Project Imports ---
from projects.mexican_groceries import config
from projects.mexican_groceries.schemas import Grade
from projects.mexican_groceries.evaluation.test_cases import TEST_CASES
from core_lib.data_sinks import JSONDataSink

# ==============================================================================
# --- GLOBAL SERVICES AND CONFIGURATION ---
# ==============================================================================

GRADER_LLM = ChatOpenAI(api_key=config.OPENAI_API_KEY, model=config.SMALL_MODEL)

DISCORD_TEST_CHANNEL_ID = config.DISCORD_TEST_CHANNEL_ID
DISCORD_TEST_BOT_USER_ID = config.DISCORD_TEST_BOT_USER_ID
DISCORD_BOT_USER_ID = config.DISCORD_BOT_USER_ID
DISCORD_TEST_BOT_TOKEN = config.DISCORD_TEST_BOT_TOKEN

LOG_FILE_PATH = (
    project_root
    / "projects"
    / "mexican_groceries"
    / "logs"
    / "e2e_run_log.jsonl"
)

DATA_SINK = JSONDataSink(log_path=LOG_FILE_PATH)

# ==============================================================================
# --- CORE FUNCTIONS ---
# ==============================================================================

async def grade_response(query: str, bot_reply: str | None) -> dict:
    """
    Uses an LLM to grade the helpfulness of the agent's response.

    Args:
        query: The original user query sent to the bot.
        bot_reply: The content of the bot's reply message.

    Returns:
        A dictionary containing the grade, reason, and score.
    """
    print("--- Grader: Evaluating response ---")

    if not bot_reply:
        print(" > Grade received: Score=0, Reason='Bot failed to reply.'")
        return {"is_helpful": False, "reason": "Bot failed to reply.", "score": 0}

    parser = JsonOutputParser(pydantic_object=Grade)

    prompt = PromptTemplate(
        template="""
You are an expert evaluator for an AI cooking assistant.
Your task is to grade the assistant's response based on the user's query.
The user's query was: "{query}"
The assistant's response was: "{response}"

Evaluate whether the response was helpful and relevant. For example:
- If the user asked for a recipe and got a shopping list, that's helpful.
- The assistant does not need to provide a recipe
- If the user asked a vague question and the assistant asked a good clarifying question, that's helpful.
- If the user's query was off-topic and the assistant correctly identified it as such and pivoted to cooking, that's helpful.
- If the user's query was off-topic and the assistant tried to create a shopping list, that's NOT helpful.

{format_instructions}
        """,
        input_variables=["query", "response"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | GRADER_LLM | parser

    try:
        grade = await chain.ainvoke({"query": query, "response": bot_reply})
        print(f" > Grade received: Score={grade['score']}, Reason='{grade['reason']}'")
        return grade
    except Exception as e:
        print(f"--- Grader: FAILED to evaluate response. Error: {e} ---")
        return {"is_helpful": False, "reason": "Grader failed to execute.", "score": 0}


# ==============================================================================
# --- E2E TESTER BOT CLASS ---
# ==============================================================================

class E2ETester(discord.Client):
    """
    A self-contained Discord client that runs a suite of E2E tests and then exits.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_channel_id = int(DISCORD_TEST_CHANNEL_ID)
        # This is the User ID of the bot we are testing.
        self.bot_under_test_id = int(DISCORD_TEST_BOT_USER_ID)
        self.test_cases = TEST_CASES
        self.total_score = 0

    async def on_ready(self):
        """Called when the tester bot has successfully connected to Discord."""
        print(f'--- E2E Tester: Logged in as {self.user} ---')
        await self.run_test_suite()
        await self.close()

    async def run_test_suite(self):
        """The main loop for running all configured test cases."""
        channel = self.get_channel(self.test_channel_id)
        if not channel:
            print(f"FATAL: Could not find channel with ID {self.test_channel_id}")
            return

        for i, case in enumerate(self.test_cases):
            print(f"\n----- Running Test Case {i+1}/{len(self.test_cases)} -----")
            print(f"ID: {case['case_id']}")
            print(f"Query: \"{case['query']}\"")

            bot_reply_content: str | None = None
            try:

                await channel.send(f"<@{DISCORD_BOT_USER_ID}> {case['query']}")

                reply = await self.wait_for(
                    "message",
                    # check=lambda m: m.author.id == self.bot_under_test_id and m.channel == channel,
                    timeout=60.0,
                )
                bot_reply_content = reply.content
                print("✅ Bot replied.")

            except asyncio.TimeoutError:
                print("❌ Test case failed: Bot did not reply in time.")

            grade = await grade_response(query=case['query'], bot_reply=bot_reply_content)

            log_entry = {
                "test_case": case,
                "bot_reply": bot_reply_content,
                "evaluation_grade": grade,
            }
            DATA_SINK.write(log_entry)
            self.total_score += grade.get("score", 0)

    def print_summary(self):
        """Prints the final summary of the test run to the console."""
        average_score = (self.total_score / len(self.test_cases)) * 100 if self.test_cases else 0
        print("\n\n========== E2E Evaluation Summary ==========")
        print(f"Total test cases: {len(self.test_cases)}")
        print(f"📈 Overall Helpfulness Score: {average_score:.2f}%")
        print("==========================================")
        print("\nE2E Evaluation complete. Check the log file for results:")
        print(f"--> {LOG_FILE_PATH}")


# ==============================================================================
# --- SCRIPT ENTRY POINT ---
# ==============================================================================

if __name__ == "__main__":
    print("--- IMPORTANT ---")
    print("Make sure your live bot is RUNNING in a separate terminal before you start this.")

    # Discord requires us to declare the 'intents' our bot needs.
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    # Initialize and run our tester bot.
    # It uses the main bot's token to log in, as it is acting on its behalf
    # to send messages and listen for replies.
    tester = E2ETester(intents=intents)

    try:
        tester.run(DISCORD_TEST_BOT_TOKEN)
        # The summary is printed only after the bot has finished its run and disconnected.
        tester.print_summary()
    except discord.errors.LoginFailure:
        print("\nFATAL: Login failed. Please check your DISCORD_BOT_TOKEN.")
    except Exception as e:
        print(f"\nAn unexpected error occurred during the E2E test run: {e}")