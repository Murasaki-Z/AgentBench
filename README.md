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