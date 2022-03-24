import time
import traceback
from pbwrap import Pastebin
import json
from pastemyst import Client, Language, Paste, Pasty, ExpiresIn, EditType
import os
#from replit import db
from inspect import getsourcefile
from os.path import abspath
    #set active directory to app location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

def getToken(tokenName):

    f = open("tokens.json")
    data = json.load(f)
    f.close()
    return data[tokenName]

#Pastebin stuff to dump error data
def pasteData(text,persistence = "ONE_HOUR"):
  client = Client(key='')
  if(persistence == "ONE_DAY"):
    res4 = client.create_paste(Paste(pasties=[Pasty('ISO', text)], expires_in=ExpiresIn.ONE_DAY))
  else:
    res4 = client.create_paste(Paste(pasties=[Pasty('ISO', text)], expires_in=ExpiresIn.ONE_HOUR))
  return("https://paste.myst.rs/"+res4.id)

def getData(key):
    f = open("db.json")
    data = json.load(f)
    return(data[key])

def updateData(key, value):
    f = open("db.json")
    data = json.load(f)
    f.close()

    data[key] = value
    
    with open("db.json", "w") as outfile:
        outfile.write(json.dumps(data, indent = 4))
    return
def listData():
  format = ("Stored data:\n")

  for key in db.keys():
    if(key.find("listofposts") == -1):
        format = format + key + ": " + str(db[key]) + "\n"
    else:
      format = format + "{}: {} items.\n".format(key,len(db[key]))
  return format
