# A2A

Agent-to-Agent communication system.

## Installation

Create a Conda env and install requirements after activating conda env:

```bash
pip install -r requirements.txt
```

## Registering API Key

Add your OpenAI API Key to env variables.
The name of the variable should be: `OPENAI_API_KEY_SDIC`

## Usage

**Terminal 1** - Start the servers:

```bash
python run_servers.py
```

**Terminal 2** - Trigger an agent:

```bash
python -m cli.trigger "Can you schedule a time with Person B and C on Feb 15?"
```

## Usage with frontend

**Terminal 1** - Start the servers:

```bash
python run_servers.py
```

**Terminal 2** - Start frontend server:

```bash
cd frontend
yarn install
yarn dev
```

Tutorial:
https://medium.com/google-cloud/a2a-deep-dive-getting-real-time-updates-from-ai-agents-a28d60317332
