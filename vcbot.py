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

class voteObject:
  def __init__(self, player, target):
    self.player = player
    self.target = target

def updateVotecount(votecount, player, target):
    for vote in votecount:
        if vote.player == player:
            votecount.remove(vote)
    votecount.append(voteObject(player,target))
    return(votecount)

def formatVotecount(votes): #generate the votecount, in format {"name":[list of players], "name":[list of players]}
    votecount = {}
    for vote in votes:
        if vote.target in votecount.keys():
            votecount[vote.target].append(vote.player)
        else:
            votecount[vote.target] = [vote.player]
    return(votecount)

def printVotecount(votes):
    votecount = formatVotecount(votes)
    text = " Votecount:\n"
    for candidate in votecount.keys():
        if(candidate != "Not voting"):
            text = text + "({}) ".format(len(votecount[candidate])) + candidate +": "
            for voter in votecount[candidate]:
                text = text+voter + ", "
            text = text[:-2] + '\n'
    try:
        candidate = "Not voting"
        text = text + "({}) ".format(len(votecount[candidate])) + candidate +": "
        for voter in votecount[candidate]:
            text = text+voter + ", "
    except:
        print("All players are voting.")
    return(text[:-1] + '\n')


def checkForHammer(votes): #return a player name if a player has been hammered, return False if no one has been hammered.
    votecount = formatVotecount(votes)
    for candidate in votecount:
        if candidate!="Not voting" and len(votecount[candidate])+1 > math.ceil((len(votes) + 1)/2):
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

    while(text.find("@") != -1):
        text = text[text.find("@"):]
        player = text[text.find("@")+1:text.find('\n')].replace(" ","")
        votecount = updateVotecount(votecount,player,"Not voting")
        text = text[text.find('\n'):]

    updateISO(gameLetter)
    print("Getting posts.")
    posts = collectAllPosts(gameLetter,page1,page2)
    print("Clearing quotes...")
    posts = clearQuotes(posts)
    print("Got posts. Calculating VC...")
    for post in posts:
        voter = post[0]
        text = post[2].lower()
        tag1 = text.rfind("[vote]")
        tag2 = text.rfind("[/vote]")

        if (tag2 > tag1 and tag2 != -1 and tag1 != -1):
            target = (text[tag1+6:tag2]).strip().replace("@","")
            #CHECK FOR ALIASES
            if(target.lower() in list_of_aliases.keys()):
              target = list_of_aliases[target.lower()]

            votecount = updateVotecount(votecount,voter,target.replace(" ", ''))
            if checkForHammer(votecount) != False:
              text = printVotecount(votecount)
              text = text + "\n**{} has been hammered.** Note that hammer checks can be disabled using the $votecount hammer off command.".format(checkForHammer(votecount))
              return(text)

    text = cycle + printVotecount(votecount)
    return(text)
  except:
    traceback.print_exc()
    errorMessage = traceback.format_exc()
    #pasteURL = pasteData(errorMessage + "\n\n\n\n\n" + str(soup))
    #updateData(("Error " + datetime.datetime.now().isoformat()),pasteURL)
    return("""Sorry, there was an error. Is the URL correct, and are the page number(s) right?
    \nIt's also possible the Hypixel website is a bit slow; check back in a bit.""")
