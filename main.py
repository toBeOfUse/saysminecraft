# add with https://discord.com/api/oauth2/authorize?client_id=999819990582710382&permissions=2147534848&scope=bot%20applications.commands
from random import choice
import disnake
from disnake.ext.commands import InteractionBot
import aiocron
from pytz import timezone

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

with open("token.txt") as token_file:
    token = token_file.read()
print("starting bot")
bot.run(token)
