# AgentBench 🔬🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/built%20with-LangChain-green.svg)](https://www.langchain.com/)

An open-source framework for building and, more importantly, **evaluating** AI agents. This project started as a personal learning journey into LangGraph and quickly evolved into a suite of practical tools for measuring and improving agent performance in a data-driven way.

The core idea is to move beyond just building agents that *work* on the happy path, and start building systems to understand *how well* they work in the real world.

This repository includes a fun example agent (`MexicanGroceries`), but the real goal is to share the evaluation tools we've built along the way.

*Here's a look at the decision graph for our example agent, which helps visualize the kind of workflows you can build and test with this framework.*
![Agent Graph Visualization](projects/mexican_groceries/evaluation/graph_visualization.png) 

---

### A Practical Approach to Agent Development

If you've worked with LLMs, you know that testing them can be tricky. They're non-deterministic, and it's hard to tell if a change you made is a real improvement or just a lucky fluke. This project is our attempt to tackle that problem head-on.

Our philosophy is simple: **good agents are built on good data**. We've focused on creating tools that help you:
1.  **Log Everything:** Capture the full context of every agent interaction.
2.  **Measure Objectively:** Define and calculate key performance indicators (KPIs) from those logs using a simple, declarative YAML configuration.
3.  **Test Continuously:** Automate the process of checking for bugs and regressions in your agent's logic.

We're sharing this in the hope that it's as useful to other developers and data professionals as it has been for our own learning.

### 🗺️ How This Repository is Organized

We've structured this project as a monorepo to keep all the related parts together. Here's a quick tour:

```
/
├── core_library/             # Reusable tools we built for the framework.
│   ├── metric_engine.py      # The engine that parses your YAML and calculates metrics.
│   ├── assertion_engine.py   # The engine for running pass/fail quality checks.
│   └── ...                   # Connectors, other tools.
│
├── projects/
│   └── mexican_groceries/    # A complete example agent to play with.
│       ├── agent.py          # The agent's core logic (built with LangGraph).
│       ├── evaluation/       # The YAML config files for testing this agent.
│       └── ...
│
└── synthetic_users/          # The scripts for running evaluations and analytics.
    ├── local_evaluator.py    # script to run batch analysis on your agent's logs.
    └── e2e_evaluator.py      # script to run tests against the live Discord bot.
```
---
### Getting Started

This guide will get you from cloning the repository to having a live agent running on Discord.

**1. Prerequisites**

You'll need Python 3.10 or newer and Git installed on your machine.

**2. Installation**

First, clone the project and move into the directory.

```bash
git clone https://github.com/your-username/AgentBench.git
cd AgentBench
```

Next, it's a good idea to create a virtual environment to keep your dependencies clean.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Now, install all the required libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

**3. Configuration**

The project uses a `.env` file to handle secret API keys. We've included a template to make this easy.

*   Find the file named `.env.example` in the main directory.
*   Make a copy of it and rename the copy to just `.env`.
*   Open your new `.env` file and fill in your own API keys. You'll need keys from OpenAI and Google (for Gemini), as well as a token for your Discord bot. The file has comments explaining each key.

**4. Running the Live Bot**

To run the Mexican Groceries bot, you first need to create a "Bot User" in the Discord Developer Portal and invite it to a server you control. Make sure to enable the "Message Content Intent" in the bot's settings.

Once your bot is invited and your `.env` file is ready, you can start the agent with this command:

```bash
python -m projects.mexican_groceries
```

Your terminal should show that the bot has logged in. You can now go to your Discord server and talk to it by mentioning its name.

### Running the Evaluation Tools

The real power of this project is in the tools that help you measure your agent.

**Analyzing Production Logs**

The `local_evaluator.py` script is a batch analyzer. It reads the `production_log.jsonl` file that your live bot creates and generates a performance summary.

To run an analysis on all the logs from the last 24 hours, use this command:

```bash
python synthetic_users/local_evaluator.py --hours 24
```

This will print a detailed reporin your console, showing you averages for your metrics and how your agent's logic paths were distributed.

**Running End-to-End Tests**

The `e2e_evaluator.py` script tests your full system by talking to your live bot through Discord.

*   **Step 1:** Make sure your live bot is running in one terminal.
*   **Step 2:** In a second terminal, run the E2E evaluator:

```bash
python synthetic_users/e2e_evaluator.py
```

This will run through the pre-defined test cases and give you a high-level quality score based on an AI grader's assessment.

### Future Ideas & Contributing

This project is an active learning journey. We have a lot of ideas for where to take it next, including:

*   Giving the main agent conversational memory to handle follow-up questions.
*   Building the autonomous "Red Team" agent to auto-generate test cases.
*   Integrating the analytics back into the agent so it can make data-driven suggestions.

If you find any bugs or have ideas for new features, feel free to open an issue.