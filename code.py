# ==================================================== Libraries ====================================================
import os
import time
import random
import discord
import logging
import requests
from bs4 import BeautifulSoup
from privatekeylmao import token
from discord.ext import commands, tasks

# ==================================================== Bot setup ====================================================
started = False
client = commands.Bot(command_prefix="&")

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Game(name = '&help for a list of commands'))
    global started
    if not started:
        started = True
        checkLoss.start()

# ==================================================== Functions ====================================================
def grabGames(user, count):
    # Gets all game placements
    allgames = []
    i = 0
    while len(allgames) < count:
        url = "https://tracker.gg/tft/profile/riot/NA/" + user + "/matches?page=" + str(i)
        request = requests.get(url)
        if request.status_code == 200:
            contents = request.text
            soup = BeautifulSoup(contents, "lxml")
            newLis = [int(e.contents[0].contents[0][0]) for e in soup.find_all("div", class_ = "result")]
            if not newLis:
                break

            allgames += newLis
            i += 1
        else:
            break

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
bullyList = {
    "Ziadom" : False,
    "TheSurge100" : False,
    "superpatel101" : False,
    "mikubestgirlll" : False
}

@tasks.loop(minutes = 5)
async def checkLoss():
    for player in bullyList:
        lastGame = grabGames(player, 1)
        if sum(lastGame) == 8: #They lost
            if not bullyList[player]:
                await client.get_channel(712110259719635024).send(player+ " recently got LAST!! HAHA what a LOSER! https://tenor.com/view/thanos-fortnite-takethel-dance-gif-12100688")
            
            bullyList[player] = True
        else:
            bullyList[player] = False

client.add_cog(Commands(client))
client.run(token)