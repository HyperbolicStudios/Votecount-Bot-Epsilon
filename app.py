import discord
import asyncio
import math
from discord.ext import tasks, commands
import datetime
import traceback
import os
from discord import app_commands
from typing import Literal
from vcbot import getVotecount
from updateData import getToken, getData, updateData
from iso import collectISO, wipeISO, updateISO, collectAllISOs, rankActivity, playerHasPosted, listPlayers

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
TOKEN = getToken("discord")

global channels
channels = {'A':[],'B':[],'C':[]}

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

async def update(text):
    print(LIST_OF_CHANNELS)
    for CHANNEL in LIST_OF_CHANNELS:
        try:
            channel = client.get_channel(int(CHANNEL))
            await channel.send(text)
        except:
            traceback.print_exc()

async def updateStatus(status):
    game = discord.Game(status)
    await client.change_presence(status=discord.Status.online, activity=game)

async def sendHelpMessage(message):
    pass

async def announce(game, text):
    for channel in channels[game]:
        await client.get_channel(channel).send(text)
    return

def is_host(interaction: discord.Interaction) -> bool:
    for role in interaction.user.roles:
        print(role)
        if("host" == role.name):
            return True
    return False

#ISO MANAGEMENT

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.check(is_host)
@app_commands.describe(game='Available Games',url="game url")
async def url(interaction: discord.Interaction, game: Literal['A', 'B', 'C'], url: str):
    updateData("url{}".format(game),url)
    wipeISO(game)
    await interaction.response.send_message('Wiped post database and Set url for game {} to {}.'.format(game,url))

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.check(is_host)
@app_commands.describe(game='Available Games')
async def wipe(interaction: discord.Interaction, game: Literal['A', 'B', 'C']):
    wipeISO(game)
    await interaction.response.send_message('Wiped ISO for game {}.'.format(game))

#ISO - PUBLIC COMMANDS

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.describe(game='Available Games')
async def update(interaction: discord.Interaction, game: Literal['A', 'B', 'C']):
    await interaction.response.send_message('Updating database for game {}. This may take a while.'.format(game))
    updateISO(game)
    channel = getChannelByName(interaction.guild,"iso-bot")
    await channel.send("Update for game {} complete.".format(game))

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.describe(game='Available Games',player = "player")
async def iso(interaction: discord.Interaction, game: Literal['A', 'B', 'C'], player: str):
    if(playerHasPosted(game,player) == True):
        text = "Found desired ISO: https://isobot.hyperbolicstudi.repl.co/{}/{} Happy scumhuntung!".format(game,player)
    else:
        text = "Nothing found for {} in game {}.".format(player,game)
    await interaction.response.send_message(text,ephemeral=True)

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.describe(game='Available Games')
async def rank_activity(interaction: discord.Interaction, game: Literal['A', 'B', 'C'],select_players: Literal['alive','all']):
    text = rankActivity(game,select_players=='active')
    await interaction.response.send_message("Ranking activity for game {}...".format(game))
    channel = getChannelByName(interaction.guild,"iso-bot")
    await channel.send(text)

#VOTECOUNT commands

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.check(is_host)
@app_commands.describe(game='Available Games',first_page="Number >= 1")
async def vc_auto_on(interaction: discord.Interaction, game: Literal['A','B','C'], first_page: int):
    await interaction.response.send_message("Auto VC for game {} set to on. First page: {}".format(game,first_page))
    updateData("vcStatus{}".format(game),"on")
    updateData("first_page"+game,first_page)
    updateData("start_time"+game, datetime.datetime.now().isoformat())

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.check(is_host)
@app_commands.describe(game='Available Games')
async def vc_auto_off(interaction: discord.Interaction, game: Literal['A','B','C']):
    await interaction.response.send_message("Auto VC for game {} set to off.".format(game))
    updateData("vcStatus"+game,"off")

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.check(is_host)
@app_commands.describe(game='Available Games',delay='Time delay in minutes')
async def vc_delay(interaction: discord.Interaction, game: Literal['A','B','C'],delay: int):
    await interaction.response.send_message("Auto VC delay for game {} set to {} minutes.".format(game, delay))
    updateData("delay"+game,delay)

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.describe(alias='alias',true_name='forum username (not case sensitive)')
async def alias(interaction: discord.Interaction, alias: str, true_name: str):
    list_of_aliases = getData("list_of_aliases")
    list_of_aliases.update({alias.lower():true_name.lower()})
    updateData("list_of_aliases",list_of_aliases)
    await interaction.response.send_message("{} is an alias of {}.".format(alias,true_name))

@tree.command(guild=discord.Object(id="951678432494911528"))
@app_commands.describe(old_name = "old forum name", new_name = "new forum name")
async def change_name(interaction: discord.Interaction, old_name: str, new_name: str):
    list_of_aliases = getData("list_of_aliases")
    for key in list_of_aliases.keys():
        if(list_of_aliases[key].lower() == old_name.lower()):
            list_of_aliases.update({key:new_name.lower()})
    updateData("list_of_aliases",list_of_aliases)
    await interaction.response.send_message("Switched name from {} to {}.".format(old_name,new_name))

@tree.command(guild=discord.Object(id="951678432494911528"))
async def alias_print(interaction: discord.Interaction):
    list_of_aliases = getData("list_of_aliases")
    format = "**List of aliases:**\n"
    for alias in list_of_aliases.keys():
        format = format+alias + "->" + list_of_aliases[alias] + "\n"
    await interaction.response.send_message(format)

@tree.command(guild=discord.Object(id="951678432494911528"))
async def getvc(interaction: discord.Interaction, game: Literal["A","B","C"],p1: int, p2: int):
    await interaction.response.send_message("Getting votecount. This might take a bit...")
    text = getVotecount(game,p1,p2)
    await interaction.channel.send(text)



"""@client.event
async def tree_eh(interaction, command, error):
    await interaction.response.send_message('Error: are you the host? Otherwise, web error')
tree.on_error = tree_eh

"""

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    #last_time = getData("last_time")
    # LIST_OF_CHANNELS = []

    for guild in client.guilds:
        print(guild.name)
        for game in ['A','B','C']:
            for channel in guild.channels:
                if channel.name == "votecount-game-"+game.lower():
                    channels[game].append(channel.id)


    print('------')
    await updateStatus("$help")
    await client.change_presence(status=discord.Status.online)
    await tree.sync(guild=discord.Object(id="951678432494911528"))
    #await updateDBs.start()
    await postVCs.start()


@client.event
async def on_message(message):
    pass

@tasks.loop(seconds = 2)
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


async def main():
    # do other async things
    # start the client
    async with client:
        await client.start(TOKEN)


asyncio.run(main())
