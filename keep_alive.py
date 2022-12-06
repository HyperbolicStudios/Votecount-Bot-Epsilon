from flask import Flask, render_template
from threading import Thread
from replit import db
from updateData import getData, getToken
from iso import collectISOinList
from flask import request

class post: #object to store post data
      def __init__(self,user,number,text_rendered,text_bbcode,id,date):
          self.user = user
          self.number = number
          self.text_rendered = text_rendered
          self.text_bbcode = text_bbcode
          self.id = id
          self.date = date

app = Flask('')
@app.route('/')
def home():
    return("I'm alive!")

@app.route("/restart")
def restart():
  return render_template("restart.html")

@app.route("/restart_now")
def restart_now():
  import os
  os.system("kill 1")
  return("Restarted")

@app.route("/db_url",methods=['POST'])
def return_url():

  api_key = request.form['key']

  if api_key == getToken('db_key'):
      print("Valid request for url made.")
      return("https://kv.replit.com/v0/eyJhbGciOiJIUzUxMiIsImlzcyI6ImNvbm1hbiIsImtpZCI6InByb2Q6MSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb25tYW4iLCJleHAiOjE2NDIzMTg2MTIsImlhdCI6MTY0MjIwNzAxMiwiZGF0YWJhc2VfaWQiOiI0OWUyNGY2MS0zNmM4LTRhYmMtYmJjNi0yZTEzNzRiZWM1ZWYifQ.xnC_OaxNUNfAF-8rMLC3Z1T9V6Lp1iGaBVQIKfQXpnK27nF8UgnZ_1GPpAwh1LLU2lrxuxWB-czORrA2cAvFgw")
  else:
    print("Error - invalid db url request made")
    return("Error - check the key.")


@app.route('/<game>/<target>')
def targetiso(game,target):


    print("getting posts...")
    posts = collectISOinList(game,target,lowerbound = -1, upperbound = 100000)
    print("got posts")
    print(len(posts))
    posts_edited = []

    for comment in posts:
      i = 0
      text_bbcode = """[QUOTE="{}, post: {}, member: 1"]{}[/QUOTE]\n""".format(comment[0],comment[3],comment[2])
      while(text_bbcode.find("""<aside class="quote">""") != -1):
        print("found quote")
        tag1 = text_bbcode.find("""<aside class="quote">""")
        tag2 = text_bbcode.find("</aside>")
        text_bbcode = text_bbcode.replace(text_bbcode[tag1:tag2+8],"")
        i=i+1
        if(i>100):
          print("Stuck in quotes loop")
         # print(comment[2])
          break

      posts_edited.append(post(comment[0],str(comment[1]),comment[2],text_bbcode,str(comment[3]),comment[4]))


    print("Rendering")
    return render_template('targetiso.html',url=getData("url"+game)+"post-", target=target,posts=posts_edited,gameletter=game)



def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
keep_alive()
