import os
from inspect import getsourcefile
from os.path import abspath
import json
import boto3
from replit import db
#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

s3 = boto3.resource(
    service_name='s3',
    region_name='us-east-2',
    aws_access_key_id=os.environ['aws_access_key_id'],
    aws_secret_access_key=os.environ['aws_secret_access_key']
)
 
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

def updateData(key,data):
    filename = "data/" + key + ".json"
    if key in ["listofpostsA","listofpostsB","listofpostsC"]:
        with open(filename, 'w') as f:
            json.dump({key:data},f)
        s3.Bucket('epsilonbucket').upload_file(Filename=filename,Key=key+".json")

    else:
        db[key] = data
    return

def getData(key):
    filename = "data/" + key + ".json"
    if key in ["listofpostsA","listofpostsB","listofpostsC"]:
        s3.Bucket('epsilonbucket').download_file(Filename = filename,Key=key+".json")
        f = open(filename)
        data = json.load(f)
        return data[key]
    else:
        return db[key]
    return

def listData():
  format = ("Stored data:\n")

  for key in db.keys():
    if(key.find("listofposts") == -1):
        format = format + key + ": " + str(db[key]) + "\n"
    else:
      format = format + "{}: {} items.\n".format(key,len(getData(key)))
  return format
