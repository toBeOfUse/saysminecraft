# add with https://discord.com/api/oauth2/authorize?client_id=999819990582710382&permissions=2147534848&scope=bot%20applications.commands
from datetime import datetime
import json
from random import choice
from pathlib import Path

import disnake
from disnake.ext.commands import InteractionBot
from disnake.ext.tasks import loop
import aiocron
from pytz import timezone
from mcstatus import JavaServer

from models import StatusBasics, BotConfig

config = BotConfig.load_from_files()

minecrafts: list[str] = ["minecraft", "Minecraft", "MINECRAFT", "Mined Craft", "Myncraft", "Minecràft"]
def get_minecraft(): return choice(minecrafts)

bot = InteractionBot()

@aiocron.crontab("0 3 * * *", tz=timezone("US/Eastern"))
async def say_minecraft():
    print("saying minecraft from loop")
    await bot.wait_until_ready()
    for guild in bot.guilds:
        await guild.text_channels[0].send(get_minecraft())

@bot.event
async def on_guild_join(guild: disnake.Guild):
    print("saying minecraft from guild join")
    await guild.text_channels[0].send(get_minecraft())

@bot.slash_command(description="Say \"Minecraft\"")
async def say_minecraft(itx):
    print("saying minecraft from slash command")
    await itx.response.send_message(get_minecraft())

server = JavaServer(config.mc_server_host, config.mc_server_port)
status_path = "./last_status.json"

@loop(seconds=30)
async def check_server():
    try:
        status_instance = await server.async_status()
    except:
        error_time = datetime.now().isoformat(timespec='seconds')
        print(f"unable to get server status at {error_time}")
        return
    status = StatusBasics(
        status_instance.players.online,
        status_instance.players.sample
    )
    last_status = StatusBasics.fromFile(status_path)
    if last_status is not None:
        new_players = set(status.sample).difference(last_status.sample)
        if ((len(new_players) > 0 and len(status.sample) < 12) or
                status.online > last_status.online):
            print("status updated to", status.toDict())
            print("saying minecraft from logged in user monitor")
            await (
                bot.get_guild(config.discord_alert_server_id)
                    .text_channels[0]
                    .send(get_minecraft())
            )
    else:
        print("established initial status:", status.toDict())
    status.toFile(status_path)

@bot.event
async def on_ready():
    print("bot ready")
    check_server.start()

print("starting bot")
bot.run(config.token)
