# A2A

Agent-to-Agent communication system.

## Installation

Create a Conda env and install requirements after activating conda env:

```bash
pip install -r requirements.txt
```

## Usage

**Terminal 1** - Start the servers:

```bash
python run_servers.py
```

**Terminal 2** - Trigger an agent:

```bash
python -m cli.trigger "Can you schedule a time with Person B and C on Feb 15?"
```

Tutorial:
https://medium.com/google-cloud/a2a-deep-dive-getting-real-time-updates-from-ai-agents-a28d60317332
