import requests
from bs4 import BeautifulSoup
import cloudscraper
import time
import datetime
import random
from updateData import getData, updateData, pasteData, getToken
import traceback
import math
from iso import updateISO, collectAllPosts, clearQuotes
import discord
class voteObject:
  def __init__(self, player, target, url):
    self.player = player
    self.target = target
    self.url = url

def updateVotecount(votecount, player, target,url):
    for vote in votecount:
        if vote.player == player:
            votecount.remove(vote)
    votecount.append(voteObject(player,target,url))
    return(votecount)

def formatVotecount(votes): #generate the votecount, in format {"name":[list of players], "name":[list of players]}
    votecount = {}
    for vote in votes:
        if vote.target in votecount.keys():
            votecount[vote.target].append(vote)
        else:
            votecount[vote.target] = [vote]
    return(votecount)

def printVotecount(votes):
    votecount = formatVotecount(votes)
    text = " Votecount:\n"
    for candidate in votecount.keys():
        if(candidate != "Not voting"):
          try:
            inc = getData("incrementsA")[candidate.lower()]
          except:
            inc = 0
          text = text + "({}) ".format(len(votecount[candidate])+inc) + candidate +": "
          for voter in votecount[candidate]:
              text = text+"[{}]({})".format(voter.player,voter.url) + ", "
          text = text[:-2] + '\n'

    incs = getData("incrementsA")
    for player in incs.keys():
        if player not in votecount.keys() and incs[player] != 0:
            text = text + "({}) {}: ???\n".format(incs[player],player)
    try:
        candidate = "Not voting"
        text = text + "({}) ".format(len(votecount[candidate])) + candidate +": "
        for voter in votecount[candidate]:
            text = text+voter.player + ", "
        text = text[:-2] + '\n'
    except:
        print("All players are voting.")
    return(text)


def checkForHammer(votes): #return a player name if a player has been hammered, return False if no one has been hammered.
    votecount = formatVotecount(votes)
    for candidate in votecount:
        try:
            inc = getData("incrementsA")[candidate.lower()]
        except:
            inc = 0
        if candidate!="Not voting" and len(votecount[candidate])+inc>= math.ceil((len(votes) + 1)/2):
            return(candidate)
    return(False)


def getVotecount(gameLetter,page1, page2=1000):
  try:
    URL = getData("url"+gameLetter)

    random.seed()

    votecount = []
    list_of_aliases = getData("list_of_aliases")
        #get list of alive voters:
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL).text

    soup = BeautifulSoup(response, 'html.parser')
    cycle = ""
    title = soup.find(class_="p-title-value").get_text()
    if(title.lower().find("day") != -1):
      cycle = "Day "+ title[title.lower().find("day")+4:title.lower().find("day")+5]
    elif(title.lower().find("night") != -1):
      cycle = "Night "+title[title.lower().find("night")+6:title.lower().find("night")+7]
    print(title)
    message = soup.find_all("article", class_='message')[0]
    text = (message.find(class_='bbWrapper')).get_text()
    text = text[text.lower().find("spoiler: living players"):text.lower().find("spoiler: dead players")]
    #print(text.encode("utf-8"))
    playerlist = []
    while(text.find("@") != -1):
        text = text[text.find("@"):]
        player = text[text.find("@")+1:text.find('\n')].replace(" ","")
        votecount = updateVotecount(votecount,player,"Not voting",0)
        playerlist.append(player)
        text = text[text.find('\n'):]
    updateData("playerlist"+gameLetter,playerlist)
    print(playerlist)
    updateISO(gameLetter)
    print("Getting posts.")
    posts = collectAllPosts(gameLetter,page1,page2)
    print("Clearing quotes...")
    posts = clearQuotes(posts)
    print("Got posts. Calculating VC...")
    for post in posts:
        voter = post[0]
        post_url = URL + "post-" +str(post[3])
        text = post[2].lower()
        tag1 = text.rfind("[vote]")
        tag2 = text.rfind("[/vote]")

        if (tag2 > tag1 and tag2 != -1 and tag1 != -1):
            target = (text[tag1+6:tag2]).strip().replace("@","")
            #CHECK FOR ALIASES
            if(target.lower() in list_of_aliases.keys()):
              target = list_of_aliases[target.lower()]

            votecount = updateVotecount(votecount,voter,target.replace(" ", ''),post_url)
            if checkForHammer(votecount) != False:
              text = printVotecount(votecount)
              text = text + "\n**{} has been hammered.** Note that hammer checks can be disabled using the $votecount hammer off command.".format(checkForHammer(votecount))
              return(text)

    text = cycle + printVotecount(votecount)
    return(discord.Embed(description=text))
  except:
    traceback.print_exc()
    errorMessage = traceback.format_exc()
    #pasteURL = pasteData(errorMessage + "\n\n\n\n\n" + str(soup))
    #updateData(("Error " + datetime.datetime.now().isoformat()),pasteURL)
    return(discord.embed(color=discord.Color.red(),description="""Sorry, there was an error. Is the URL correct, and are the page number(s) right?
    \nIt's also possible the Hypixel website is a bit slow; check back in a bit.\n\nError message: """+errorMessage)


def updatePlayerlist(gameLetter):
    URL = getData("url"+gameLetter)
    scraper = cloudscraper.create_scraper()
    response = scraper.get(URL).text
    soup = BeautifulSoup(response, 'html.parser')

    message = soup.find_all("article", class_='message')[0]
    text = (message.find(class_='bbWrapper')).get_text()
    text = text[text.lower().find("spoiler: living players"):text.lower().find("spoiler: dead players")]
    playerlist = []
    while(text.find("@") != -1):
        text = text[text.find("@"):]
        player = text[text.find("@")+1:text.find('\n')].replace(" ","")

        playerlist.append(player.lower())
        text = text[text.find('\n'):]
    updateData("playerlist"+gameLetter,playerlist)
    return(playerlist)
