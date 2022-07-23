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
from mcstatus.pinger import PingResponse

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

with open("server.json") as server_file:
    server_data = json.load(server_file)
server = JavaServer(server_data["host"], server_data["port"])

class StatusBasics():

    class Player():

        def __init__(self, name: str, id: str):
            self.name = name
            self.id = id

        def __hash__(self) -> int:
            return hash(self.id)
        
        def __eq__(self, other: "StatusBasics.Player"):
            return self.id == other.id

        def toDict(self) -> dict:
            return { "name": self.name, "id": self.id }
        
    def __init__(self, online: int, sample: list[PingResponse.Players.Player]):
        self.online = online
        self.sample = (
            [StatusBasics.Player(x.name, x.id) for x in sample]
                if sample is not None
                else []
        )
    
    def toDict(self) -> dict:
        return {"online": self.online, "sample": [x.toDict() for x in self.sample]}
    
    @classmethod
    def fromDict(cls, src: dict):
        return cls(
            src["online"], 
            [PingResponse.Players.Player(x) for x in src["sample"]]
        )


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
    last_status_path = Path("./last_status.json")
    if last_status_path.exists():
        with open(last_status_path) as last_status_file:
            last_status = StatusBasics.fromDict(json.load(last_status_file))
        new_players = set(status.sample).difference(last_status.sample)
        if len(new_players) > 0 or status.online > last_status.online:
            await (
                bot.get_guild(999812620775346226)
                # bot.get_guild(708955889276551198)
                    .text_channels[0]
                    .send(get_minecraft())
            )
    with open(last_status_path, mode="w+", encoding="utf-8") as last_status_file:
        json.dump(status.toDict(), last_status_file)

@bot.event
async def on_ready():
    print("bot ready")
    check_server.start()

with open("token.txt") as token_file:
    token = token_file.read()
print("starting bot")
bot.run(token)
