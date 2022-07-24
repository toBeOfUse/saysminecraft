# add with https://discord.com/api/oauth2/authorize?client_id=999819990582710382&permissions=2147534848&scope=bot%20applications.commands
import asyncio
from datetime import datetime
import json
from pathlib import Path

import disnake
from disnake.ext.commands import InteractionBot
from disnake.ext.tasks import loop
import aiocron
from pytz import timezone
from mcstatus import JavaServer
from tinydb import TinyDB, where

from models import StatusBasics, BotConfig, get_minecraft

config = BotConfig.load_from_files()

bot = InteractionBot()

db = TinyDB("./last_message.tinydb")

def set_last_message(channel_id: int, message_id: int):
    existing = db.search(where("channel_id") == channel_id)
    if len(existing) > 0:
        async def fun():
            channel = await bot.fetch_channel(channel_id)
            message = await channel.fetch_message(existing[0]["message_id"])
            await message.delete()
        asyncio.create_task(fun())
    db.upsert(
        {"channel_id": channel_id, "message_id": message_id}, 
        where("channel_id") == channel_id
    )

@aiocron.crontab("0 3 * * *", tz=timezone("US/Eastern"))
async def say_minecraft():
    print("saying minecraft from loop")
    await bot.wait_until_ready()
    for guild in bot.guilds:
        channel = guild.text_channels[0]
        message = await channel.send(**get_minecraft())
        set_last_message(channel.id, message.id)

@bot.event
async def on_guild_join(guild: disnake.Guild):
    print("saying minecraft from guild join")
    await guild.text_channels[0].send(**get_minecraft())

@bot.slash_command(description="Say \"Minecraft\"")
async def say_minecraft(itx: disnake.ApplicationCommandInteraction):
    print("saying minecraft from slash command")
    minecraft = get_minecraft()
    if minecraft.large():
        await itx.response.defer(ephemeral=False)
        message = await itx.original_message()
        set_last_message(itx.channel_id, message.id)
        await itx.edit_original_message(**minecraft)
    else:
        await itx.response.send_message(**minecraft)
        message = await itx.original_message()
        set_last_message(itx.channel_id, message.id)

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
            channel = (
                bot.get_guild(config.discord_alert_server_id)
            ).text_channels[0]
            message = await channel.send(**get_minecraft())
            set_last_message(channel.id, message.id)
    else:
        print("established initial status:", status.toDict())
    status.toFile(status_path)

@bot.event
async def on_ready():
    print("bot ready")
    check_server.start()

print("starting bot")
bot.run(config.token)
