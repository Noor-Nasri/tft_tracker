# ==================================================== Libraries ====================================================
import os
import time
import random
import discord
import logging
import requests
import keep_alive
from bs4 import BeautifulSoup
from privatekeylmao import token
from discord.ext import commands, tasks

# ==================================================== Bot setup ====================================================
started = False
client = commands.Bot(command_prefix="%")

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Game(name = '%help for a list of commands'))
    global started
    if not started:
        started = True
        checkLoss.start()

# ==================================================== Functions ====================================================
bullyList = {
    "Ziadom" : [[0], False],
    "TheSurge100" : [[0], False],
    "superpatel101" : [[0], False],
    "mikubestgirlll" : [[0], False],
    "KFC_main" : [[0], False]
}

def grabGames(user, count, retry = False):
    # Gets all game placements
    allgames = None
    if retry or user not in bullyList:
        uniqueTimes = set()
        allgames = []
        i = 0
        c = 0

        while len(allgames) < count and c < 3:
          url = "https://tracker.gg/tft/profile/riot/NA/" + user.replace("_", "%20") + "/matches?page=" + str(i)
          request = requests.get(url)
          if request.status_code == 200:
              contents = request.text
              soup = BeautifulSoup(contents, "lxml")
              origList = soup.find_all("div", class_ = "result")
              newLis = []
              for e in origList:
                if not e.contents[2].get("title") in uniqueTimes:
                  uniqueTimes.add(e.contents[2].get("title"))
                  newLis.append(int(e.contents[0].contents[0][0]))

              if not origList:
                break
              allgames += newLis
              i += 1
          else:
              print("Bad request, trying again")
              c+=1
                
        if len(allgames) == 0:
          allgames = [0]
          print("Found no games for", user)

    else:
        allgames = bullyList[user][0]

    return allgames[:count]

def getScore(user):
    scores = grabGames(user, 20)
    score = 0
    for item in scores:
        score += 8 - item
    return score

def sortNub(k):
    return k[1]

# ==================================================== Commands ====================================================
class Commands(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command(help = "[username] scores the user based on their 20 games")
    async def score(self, ctx, arg):
        points = getScore(arg)
        await ctx.channel.send(arg + "'s score in the last 20 games is " + str(points) + " (average placement: " + str(8-round(points/20, 2)) + ")")

    @commands.command(help = "[username] averages all their matches in history")
    async def average(self, ctx, arg):
        points = grabGames(arg, 300)
        await ctx.channel.send(arg + "'s lifetime average placement is: " + str(round(sum(points)/len(points), 2)))    
    
    @commands.command(help = "[username] gives the number of games played")
    async def count(self, ctx, arg):
        points = grabGames(arg, 100000000)
        await ctx.channel.send(arg + " has played " + str(len(points)) + " games")    

    @commands.command(help = "[username] gives the odds of the player winning")
    async def win_rate(self, ctx, arg):
        points = grabGames(arg, 100000000)
        await ctx.channel.send(arg + " wins once in " + str(round(1/(points.count(1)/len(points)), 2))  + " games")    

    @commands.command(help = "[username] [x] for the number of wins in last x games (default lifetime)")
    async def wins(self, ctx, *args):
        user, x = None, None
        if len(args) == 1:
            user = args[0]
            x = 300
        else:
            user, x = args
            x = min(int(x), 300)

        await ctx.channel.send(user + " has won " +  str(grabGames(user, x).count(1)) + " of the last " + str(x) + " games.")
    
    
    @commands.command(help = "[recent / legacy / wins / win_rate] for leaderboards")
    async def leaderboard(self, ctx, arg):
        scoring = []
        for name in bullyList:
            if arg == "recent" or arg == "legacy" or arg == "win_rate": #points
                points = grabGames(name, arg == "recent" and 10 or 300000)
                if arg == "win_rate":
                    scoring.append([name, round(points.count(1)/len(points), 2)])
                else:
                    scoring.append([name, round(sum(points)/len(points), 2)])
            
            else: #wins
                scoring.append([name, grabGames(name, 300).count(1)])
        
        scoring = sorted(scoring, key=sortNub)
        if not(arg == "recent" or arg == "legacy"):
            scoring = scoring[::-1]
        
        text = "```" + "\n" + arg + ": \n"
        for i in range(len(scoring)):
            text += str(i + 1) + ") " + scoring[i][0] + ": " + str(scoring[i][1])  + "\n"

        await ctx.channel.send(text + "```")   

#-------Background Tasks-------
@tasks.loop(minutes = 6)
async def checkLoss():
    for player in bullyList:
        if bullyList[player][0][:5] != grabGames(player, 5, True): #Update list
            newValues = [[], False]
            for a in range(3):
              print("Rechecking", player)
              newValues[0] = grabGames(player, 300, True)
              if len(newValues[0]) > len(bullyList[player][0]) :
                done = True
                break
                
            if not done:
              print("Asking for help", player, newValues)
              await client.get_channel(712110259719635024).send("Things are going wrong, ping noor for me")
              break

            bullyList[player] = newValues

        if bullyList[player][0][0] == 8: #They lost
            if not bullyList[player][1]:
                await client.get_channel(712110259719635024).send(player+ " recently got LAST!! HAHA what a LOSER! https://tenor.com/view/thanos-fortnite-takethel-dance-gif-12100688")
            
            bullyList[player][1] = True
    
    print("Done")

keep_alive.keep_alive()
client.add_cog(Commands(client))
client.run(token)
