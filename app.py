import discord
import asyncio
import math
from discord.ext import tasks, commands
import datetime
import traceback
import os
from keep_alive import keep_alive
from discord import app_commands
from typing import Literal
from vcbot import getVotecount
from updateData import getToken, getData, updateData
from iso import wipeISO, updateISO, collectAllISOs, rankActivity, playerHasPosted, listPlayers
from queue_manager import get_queue
intents = discord.Intents.default()
intents.message_content = True
help_message = discord.Embed(
    colour=discord.Color.teal(),
    description = """
    Epsilon is a combined votecount and ISO bot. It simultaneously handles three games (named A, B, and C), handles ISOs, posts automatic and manual votecounts, and checks for any hammers that occur.

    Note for mods: please ensure that the "Living Players" spoiler is up-to-date in the OP, as the bot uses that list to determine if a hammer has occured.

    Also note that due to popular request, the [unvote] tag has been disabled.

    **Mod Commands** *Requires the user to be the host or part of the mod team*\n
    `/url <game> <url>` - sets the game URL.\n
    `/wipe <game>` - wipes the ISO database.\n
    `/vc_auto_on <game> first_page>` - turns on the auto VC function.\n
    `/vc_auto_off <game>` - turns it off.\n
    `/vc_delay <game> <delay>` - sets the auto VC delay in minutes.\n
    `/queue_init` - updates the queue. (Mod team use only)\n\n

    **Public Commands** *Anyone can use these.*\n
    `/updateISO <game>` - manually updates the ISO database for that game.\n
    `/iso <game> <player>` - links you to the ISO for that player.\n
    `/rank_activity <game>` - lists every player and their postcount.\n
    `/alias <alias> <truename>` - create an alias for a player.\n
    `/change_name old_name new_name` - if you change your forum name, use this command to shift all your old aliases to your new name.\n
    `/alias_print` - prints all aliases stored.\n
    `/getvc <game> <p1> <p2>` - gets a votecount for that game, from page 1 to page 2.
    """
    )

keep_alive()
TOKEN = getToken("discord")

global channels
channels = getData("channels")

def getChannelByName(guild,name):
    for channel in guild.channels:
        if(channel.name) == name:
            return channel
    return(0)

def getRoleByName(guild,name):
    for role in guild.roles:
        if(role.name == name):
          return(role)
    return(0)

async def updateStatus(status):
    game = discord.Game(status)
    await client.change_presence(status=discord.Status.online, activity=game)
    print("Updated status to {}".format(status))
    return


async def announce(game, text):
    for channel in channels[game]:
        await client.get_channel(channel).send(text)
    return

def is_host(interaction: discord.Interaction) -> bool:
    for role in interaction.user.roles:
        print(role)
        if(role.name in ["Mafia","Puppeteer (Host)"]):
            return True
    return False

async def postVCs():
    for game in ["A","B","C"]:
        delta = round((datetime.datetime.now()-datetime.datetime.fromisoformat(getData("last_time"+game))).total_seconds())
        timeSpentOn = round((datetime.datetime.now()-datetime.datetime.fromisoformat(getData("start_time"+game))).total_seconds())
        print("delta: {}    timeSpentOn: {}   status: {}".format(delta,timeSpentOn,getData("vcStatus"+game)))
        if(getData("vcStatus"+game) == "on" and timeSpentOn > 3600*48): #turn off after 48 hours
            print("AUTO VOTECOUNTS TURNED OFF BY TIMER")
            await announce(game,"The automatic votecount has been on for 48 consecutive hours. It will now turn off. Use $votecount auto on <page number> to resume, or $votecount <firstpage> <lastpage> to generate a single votecount.")
            updateData("vcStatus","off")

        if (getData("vcStatus"+game) == "on" and delta > getData("delay"+game) * 60):
            print("Scanning")
            await announce(game,"Getting a votecount. This may take some time. First page: " + str(getData("first_page"+game)))
            votecount = getVotecount(game,getData("first_page"+game),1000)
            await announce(game,votecount)
            await announce(game,"The next votecount will be processed in " + str(getData("delay"+game) / 60) + " hours. You can view this votecount and all previous votecounts in the #votecounts channel in Discord.")
            updateData("last_time"+game, datetime.datetime.now().isoformat())
    return

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        # start the task to run in the background
      self.my_background_task.start()

    @tasks.loop(seconds=5) # task runs every 5 seconds
    async def my_background_task(self):
        await postVCs()

client = MyClient()
tree = app_commands.CommandTree(client)
#ISO MANAGEMENT

@tree.command()
@app_commands.check(is_host)
@app_commands.describe(game='Available Games',url="game url")
async def url(interaction: discord.Interaction, game: Literal['A', 'B', 'C'], url: str):
    updateData("url{}".format(game),url)
    wipeISO(game)
    await interaction.response.send_message('Wiped post database and Set url for game {} to {}.'.format(game,url))

@tree.command()
@app_commands.check(is_host)
async def queue_init(interaction: discord.Interaction):
  await interaction.response.send_message("Updating!",ephemeral=True)
  for guild in client.guilds:
    for channel in guild.channels:
      if channel.name == "mafia-hosting-queues":
        print("-------------")
        queues = getData("queues")
        if queues is None:
          queues = {}
        if str(channel.id) in list(queues.keys()):
          try:
            msg = await channel.fetch_message(queues[str(channel.id)])
            await msg.edit(content=get_queue())
          except:
            msg = await channel.send(get_queue())
            queues.update({channel.id:str(msg.id)})
            updateData("queues",queues)
            print("New queue msg created.")

        else:
          msg = await channel.send(get_queue())
          queues.update({channel.id:str(msg.id)})
          updateData("queues",queues)
          print("New queue msg created.")


@tree.command()
@app_commands.check(is_host)
@app_commands.describe(game='Available Games')
async def wipe(interaction: discord.Interaction, game: Literal['A', 'B', 'C']):
    wipeISO(game)
    await interaction.response.send_message('Wiped ISO for game {}.'.format(game))

#ISO - PUBLIC COMMANDS

@tree.command()
@app_commands.describe(game='Available Games')
async def update(interaction: discord.Interaction, game: Literal['A', 'B', 'C']):
    await interaction.response.send_message('Updating database for game {}. This may take a while.'.format(game))
    updateISO(game)
    channel = getChannelByName(interaction.guild,"iso-bot")
    await channel.send("Update for game {} complete.".format(game))

@tree.command()
@app_commands.describe(game='Available Games',player = "player")
async def iso(interaction: discord.Interaction, game: Literal['A', 'B', 'C'], player: str):
    if(playerHasPosted(game,player) == True):
        text = "Found desired ISO: https://orbit-epsilon.hyperbolicstudi.repl.co//{}/{} Happy scumhuntung!".format(game,player)
    else:
        text = "Nothing found for {} in game {}.".format(player,game)
    await interaction.response.send_message(text,ephemeral=True)

@tree.command()
@app_commands.describe(game='Available Games')
async def rank_activity(interaction: discord.Interaction, game: Literal['A', 'B', 'C'],select_players: Literal['alive','all']):
    text = rankActivity(game,select_players=='active')
    await interaction.response.send_message("Ranking activity for game {}...".format(game))
    channel = getChannelByName(interaction.guild,"iso-bot")
    await channel.send(text)

#VOTECOUNT commands

@tree.command()
@app_commands.check(is_host)
@app_commands.describe(game='Available Games',first_page="Number >= 1")
async def vc_auto_on(interaction: discord.Interaction, game: Literal['A','B','C'], first_page: int):
    await interaction.response.send_message("Auto VC for game {} set to on. First page: {}".format(game,first_page))
    updateData("vcStatus{}".format(game),"on")
    updateData("first_page"+game,first_page)
    updateData("start_time"+game, datetime.datetime.now().isoformat())

@tree.command()
@app_commands.check(is_host)
@app_commands.describe(game='Available Games')
async def vc_auto_off(interaction: discord.Interaction, game: Literal['A','B','C']):
    await interaction.response.send_message("Auto VC for game {} set to off.".format(game))
    updateData("vcStatus"+game,"off")

@tree.command()
@app_commands.check(is_host)
@app_commands.describe(game='Available Games',delay='Time delay in minutes')
async def vc_delay(interaction: discord.Interaction, game: Literal['A','B','C'],delay: int):
    await interaction.response.send_message("Auto VC delay for game {} set to {} minutes.".format(game, delay))
    updateData("delay"+game,delay)

@tree.command()
@app_commands.describe(alias='alias',true_name='forum username (not case sensitive)')
async def alias(interaction: discord.Interaction, alias: str, true_name: str):
    list_of_aliases = getData("list_of_aliases")
    list_of_aliases.update({alias.lower():true_name.lower()})
    updateData("list_of_aliases",list_of_aliases)
    await interaction.response.send_message("{} is an alias of {}.".format(alias,true_name))

@tree.command()
@app_commands.describe(old_name = "old forum name", new_name = "new forum name")
async def change_name(interaction: discord.Interaction, old_name: str, new_name: str):
    list_of_aliases = getData("list_of_aliases")
    for key in list_of_aliases.keys():
        if(list_of_aliases[key].lower() == old_name.lower()):
            list_of_aliases.update({key:new_name.lower()})
    updateData("list_of_aliases",list_of_aliases)
    await interaction.response.send_message("Switched name from {} to {}.".format(old_name,new_name))

@tree.command()
async def alias_print(interaction: discord.Interaction):
    list_of_aliases = getData("list_of_aliases")
    format = "**List of aliases:**\n"
    for alias in list_of_aliases.keys():
        format = format+alias + "->" + list_of_aliases[alias] + "\n"
    await interaction.response.send_message(format)

@tree.command()
async def getvc(interaction: discord.Interaction, game: Literal["A","B","C"],p1: int, p2: int):
    await interaction.response.send_message("Getting votecount. This might take a bit...")
    text = getVotecount(game,p1,p2)
    await interaction.channel.send(text)

@tree.command()
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=help_message,ephemeral=True)


"""@client.event
async def tree_eh(interaction, command, error):
    await interaction.response.send_message('Error: are you the host? Otherwise, web error')
tree.on_error = tree_eh
"""


@client.event
async def on_ready():
    await updateStatus("/help")
    await client.change_presence(status=discord.Status.online)
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    #last_time = getData("last_time")
    channels = {'A':[],'B':[],'C':[]}
    for guild in client.guilds:
        print(guild.name)
        for game in ['A','B','C']:
            for channel in guild.channels:
                if channel.name == "votecount-game-"+game.lower():
                    channels[game].append(channel.id)
    updateData("channels",channels)

    print('------')

    await tree.sync()
    #await tree.sync(guild=discord.Object(id="951678432494911528"))
    #await updateDBs.start()



client.run(getToken("discord"))
