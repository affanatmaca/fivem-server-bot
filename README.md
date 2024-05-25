# FiveM Server Bot

This is a Discord bot written in Python using the `discord.py` library. The bot provides a ticket system for your server, allowing members to create, manage, and close tickets. This bot also includes various logging functionalities for emojis, messages, and voice channel activities, specifically tailored for FiveM server communities.

## Features

- Create and manage tickets
- Log emoji usage
- Log messages and channel activities
- Manage member roles and approvals
- Notify staff members of new registrations and support requests

## Prerequisites

- Python 3.8 or higher
- `discord.py` library
- `python-dotenv` library

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/affanatmaca/fivem-server-bot.git
    cd fivem-server-bot
    ```

2. Install the required packages:
    ```bash
    pip install discord.py python-dotenv
    ```

3. Create a `.env` file in the root directory and add your Discord bot token:
    ```
    DISCORD_BOT_TOKEN=your-bot-token
    ```

4. Update the `main.py` file with your server and channel IDs.

## Usage

Run the bot using:
```bash
python main.py
```

This project is fully english. if you want lookup for turkish project check this link https://github.com/affanatmaca/fivem-server-bot-turkish/
