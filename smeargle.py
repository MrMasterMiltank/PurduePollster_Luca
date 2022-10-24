# Python 3.8.3, Red Bot 3.4.18, discord.py 1.7.3

from redbot.core import commands

import asyncio
import discord

import aiohttp
import ast
import csv
import cv2 as cv
import datetime as dt
import enchant
import imutils
import io
import json
import math
import numpy as np
import os
import pytesseract as tes
import re
import shutil

from datetime import timedelta, datetime
from difflib import SequenceMatcher
from discord.utils import get
from fuzzywuzzy import fuzz

#---------------------------------------------------------------------------------#
#---------------------------------Local Settings----------------------------------#
#---------------------------------------------------------------------------------#

tes.pytesseract.tesseract_cmd = r"I:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
# path to the cogs
cogPath = "I:\\PurdueTest\\cogs\\CogManager\\cogs\\"
# path to the config json files
configPath = cogPath + "configs\\"
# path to this python script
smearglePath = cogPath + "smeargle.py"
# path to the game master file
GMPath = configPath + "GAME_MASTER.json"
# word dictionary
wordDict = enchant.Dict("en_US") 

#---------------------------------------------------------------------------------#
#-------------------------------Channel Settings----------------------------------#
#---------------------------------------------------------------------------------#

# server id, this bot will only serve one server
#serverId = 730448547014639646
# user ids overrides
lucaId = 282002735862382592
# channel ids
# raid-sightings channel id
sightingChanId = 641135454305124353
# raid-role-signups channel id
signupChanId = 1033408042819145869
# active-raids channel id
activeChanId = 641163543231725578
# all raid-channel ids
raidChanIds = [
    641129991534280724,641129969216389121,641129980306259968,641129929164980235,641129958051151892,641129946475134976,641129919065358358,641129484107382794,641129497227165732,641129210454212609,641128903556988929,641128889296486450,
    641130294191325194,641130339653255179,641130302240194579,641130351951085589,641130285378830355,641130325577039873,641130315112382464,641130248813150209,641130274855452696,641130262968664092,641130009666256934,641129999830876181,  
    641128880161161227,641128916068728833,641128867360276511,641128798041014282,641128785332273182,641128772338319360,641128757096349696,641128743473119273,641128731187871792,641128657296818188,641128642621210634,641128364685393952
]
# bot-debug channel id
debugChanId = 641155282285625356
# channels where commands by everyone are potentially allowed
allChanIds = raidChanIds.copy()
allChanIds.extend([sightingChanId])
# category ids
# warehouse category id
warehouseId = 1033411036939829258
# raid channels category id
raidCategoryId = 1033411177843282041
# role ids
# shiny role name
raidShinyName = "PossShiny"
# raid role ids
roleIds = {
    "RaidLevel5" : 403577542302498867,
    "RaidElite" : 1033410226520608848,
    "RaidMega" : 748534319269806102,
    raidShinyName : 1033413040705642517,
    "Level5" : [1033412062254207046, 1033774008774180894, 1033774035118592080, 1033774075870449745, 1033774116353875968],
    "Elite" : [1033412735586795600, 1033774677023268864, 1033774715652804618],
    "Mega" : [1033774564699811880, 1033774599944544256, 1033774637793943612],
    "Level4" : [403944168738652170],
    "Level3" : [403944208727277569, 1033774190127480862, 1033774237720252496, 1033774290904043562, 1033774334323474532],
    "Level1" : [1033774382952222720, 1033774422840066098, 1033774461431840889, 1033774490825539715, 1033774524010860544],
}
tierNames = {
    "SuperMega" : 6,
    "Elite" : 6,
    "Level5" : 5,
    "Mega" : 4,
    "Level4" : 4,
    "Level3" : 3, 
    "Level1" : 1,
}
tierNamesShort = ["Level1", "Level3", "Level4", "Mega", "Elite", "Level5"]
inPersonTierNames = ["Level4", "Elite"]
regionIds = {
    "North" : {
        "id" : 338883202775121920,
        "parent" : "",
    },
    "Kent" : {
        "id" : 338883317158117376,
        "parent" : "",
    },
    "South" : {
        "id" : 338883376264118272,
        "parent" : "",
    },
    "Brown" : {
        "id" : 375672297408954389,
        "parent" : "North",
    },
    "Newport" : {
        "id" : 338883421889626113,
        "parent" : "",
    },
    "Uri" : {
        "id" : 412451827364265994,
        "parent" : "South",
    },
    "RWP" : {
        "id" : 471298490631323659,
        "parent" : "North",
    },
    "Westerly" : {
        "id" : 471298539000168448,
        "parent" : "South",
    },
    "Downtown" : {
        "id" : 487338277100191744,
        "parent" : "North",
    },
    "Covww" : {
        "id" : 471299098474053633,
        "parent" : "Kent",
    },
    "PCRIC" : {
        "id" : 471307903471452170,
        "parent" : "North",
    }
}
        
#---------------------------------------------------------------------------------#
#----------------------------Raid Function Settings-------------------------------#
#---------------------------------------------------------------------------------#

# time formats
# used in the raid channel top embed
timeForm = "%m/%d/%Y %I:%M:%S %p"
# used in the active raids embeds
timeFormShorter = "%I:%M %p"
# time constants
# time zone of the bot
timeZoneHours = -4 # hours
# the bot will not listen to raid input for this many seconds after the last one
raidCooldownSeconds = 2 # seconds
# the bot will check the time on an active raid channel every this many seconds
monitorCooldownSeconds = 180 # seconds
# active channels will be deactivated this many minutes after the raid end time
deleteMinutes = 5 # minutes
# when waiting for user input, timeout after this many seconds
timeoutSeconds = 30 # seconds
# when a channel is returned to the warehouse from the active raid category, it will have a cooldown time of this many minutes
chanCooldownMinutes = 5 # minutes
# when a channel has this many minutes left, the color of embed will change to caution
cautionMinutes = 20 # minutes
# when a channel has this many minutes left, the color of embed will change to urgent
urgentMinutes = 10 # minutes
# check in advance this many hours for schedules
advanceHours = 18 # hours
# check back this many hours for schedules
backHours = -6 # hours
# permissible emojis
# number emojis used to easily indicate a number input
accountEmoji = [b"1\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"), b"2\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"), b"3\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"),
                b"4\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"), b"5\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"), b"6\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"),
                b"7\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"), b"8\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"), b"9\xef\xb8\x8f\xe2\x83\xa3".decode("utf-8"),
                b"\xf0\x9f\x94\x9f".decode("utf-8"), b"\xf0\x9f\x95\x9a".decode("utf-8")]
# frown face
errorEmoji = b"\xe2\x98\xb9\xef\xb8\x8f".decode("utf-8")
# thumbs up
okayEmoji = b"\xf0\x9f\x91\x8d".decode("utf-8")
# red exclamation mark
notifEmoji = b"\xe2\x9d\x97".decode("utf-8")
# free raid pass
inpersonEmojiName = "EX"
inpersonEmojiString = b"\xf0\x9f\x99\x8b\xe2\x80\x8d\xe2\x99\x80\xef\xb8\x8f".decode("utf-8")
inpersonEmojiId = 440549150111694859
remoteEmojiName = "SphealTeam6"
remoteEmojiString = b"\xf0\x9f\xa5\xb7".decode("utf-8")
remoteEmojiId = 611289746093768842
hostEmojiName = "RIPoGo"
hostEmojiString = b"\xf0\x9f\xa7\x99\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f".decode("utf-8")
hostEmojiId = 440510352799694859
# raid levels
raidLevels = {
    "Level1" : {"raidTimer" : 45, "url" : r"https://www.serebii.net/pokemongo/items/normalegg.png"},
    "Level3" : {"raidTimer" : 45, "url" : r"https://www.serebii.net/pokemongo/items/rareegg.png"},
    "Level4" : {"raidTimer" : 45, "url" : r"https://github.com/PokeMiners/pogo_assets/blob/master/Images/Raids/raid_egg_5_icon.png?raw=true"},
    "Level5" : {"raidTimer" : 45, "url" : r"https://www.serebii.net/pokemongo/items/legendaryegg.png", "role" : "RaidLevel5"},
    "Elite" : {"raidTimer" : 30, "url" : r"https://www.serebii.net/pokemongo/items/eliteegg.png", "role" : "RaidElite"},
    "Mega" : {"raidTimer" : 45, "url" : r"https://www.serebii.net/pokemongo/items/megaegg.png", "role" : "RaidMega"},
    "SuperMega" : {"raidTimer" : 45, "url" : r"https://www.serebii.net/pokemongo/items/megaegg.png", "role" : "RaidMega"},
}
# text settings
# colors for embed
defaultColor = 0x00ff00
cautionColor = 0xffff00
urgentColor = 0xff0000
# for group embed
groupHostText = "__Host__"
groupInpersonText = "__In-Person Sign-ups__"
groupRemoteText = "__Remote Sign-ups__"
groupNooneText = "No one yet"
# for active embed
activeStartText = "__Start Time__"
activeEndText = "__End Time__"
activeChannelText = "__Raid Channel__"
activeSignupText = "__Current Sign-ups__"
# for raid top embed
raidWeaknessText = "__Weaknesses__"
raidCPText = "__Catch CP__"
instructionText = "__Instructions__"
mapText = "__Google Map__"
# other common messages
cacheText = "Bot recently restarted, rebuilding message cache, please stand by..."
cooldownText = notifEmoji + " Bot is in cooldown, please try again in 3 seconds."
# confidence numbers
confidenceRaw = 0.85
confidenceRelative = 0.7
confidenceLower = 0.6
confidenceRelativeLower = 0.4

#---------------------------------------------------------------------------------#
#-------------------------Pokemon Function Settings-------------------------------#
#---------------------------------------------------------------------------------#

# path to the pokemon images on serebii
imgPath = r"https://serebii.net/pokemongo/pokemon/"
imgPathShiny = r"https://serebii.net/pokemongo/pokemon/shiny/"
# types dictionary, used to convert type name strings to indices
typeDict = {
    "POKEMON_TYPE_NORMAL" : 1, 
    "POKEMON_TYPE_FIGHTING" : 2,
    "POKEMON_TYPE_FLYING" : 3,
    "POKEMON_TYPE_POISON" : 4,
    "POKEMON_TYPE_GROUND" : 5,
    "POKEMON_TYPE_ROCK" : 6,
    "POKEMON_TYPE_BUG" : 7,
    "POKEMON_TYPE_GHOST" : 8,
    "POKEMON_TYPE_STEEL" : 9,
    "POKEMON_TYPE_FIRE" : 10,
    "POKEMON_TYPE_WATER" : 11,
    "POKEMON_TYPE_GRASS" : 12,
    "POKEMON_TYPE_ELECTRIC" : 13,
    "POKEMON_TYPE_PSYCHIC" : 14,
    "POKEMON_TYPE_ICE" : 15,
    "POKEMON_TYPE_DRAGON" : 16,
    "POKEMON_TYPE_DARK" : 17,
    "POKEMON_TYPE_FAIRY" : 18
}
# names that will overwrite the default pokemon name
overwriteNames = [
    "WORMADAM_PLANT",
    "GIRATINA_ALTERED",
    "SHAYMIN_LAND",
    "DARMANITAN_STANDARD",
    "TORNADUS_INCARNATE",
    "THUNDURUS_INCARNATE",
    "LANDORUS_INCARNATE",
    "MELOETTA_ARIA",
    "PUMPKABOO_SMALL",
    "GOURGEIST_SMALL",
    "HOOPA_CONFINED",
    "ORICORIO_BAILE",
    "LYCANROC_MIDDAY",
    "WISHIWASHI_SOLO",
    "EISCUE_ICE" 
]
# battle constant settings from the game master file
timeDefenderCool = 200
timeAttackerWait = 50
timeDefenderWait = 150
timeAttackerSwap = 250
energyMax = 100
multSTAB = 1.2
multDmgEnergy = 0.5
multShadowAtt = 1.2
multShadowDef = 0.8333333
multPvPAtt = 1.3
# buff/debuff settings
multBuff = {
    -4 : 0.5,
    -3 : 0.5714286,
    -2 : 0.6666667,
    -1 : 0.8,
    0  : 1.0,
    1  : 1.25,
    2  : 1.5,
    3  : 1.75,
    4  : 2.0
}
# friendship settings
multFriendship = [1.05, 1.08, 1.1, 1.12, 1.15]
# CPM settings
# lvl = int(level * 2)
# level = lvl / 2.0
CPM = [
    0.0, 0.0,
    0.094, 0.135137432, 0.16639787, 0.192650919, 0.21573247,
    0.236572613, 0.25572005, 0.273530381, 0.29024988, 0.306057378,
    0.3210876, 0.335445036, 0.34921268, 0.362457751, 0.3752356,
    0.387592416, 0.39956728, 0.411193551, 0.4225, 0.432926409,
    0.44310755, 0.453059959, 0.4627984, 0.472336093, 0.48168495,
    0.4908558, 0.49985844, 0.508701765, 0.51739395, 0.525942511,
    0.5343543, 0.542635738, 0.5507927, 0.558830586, 0.5667545,
    0.574569133, 0.5822789, 0.589887907, 0.5974, 0.604823665,
    0.6121573, 0.619404122, 0.6265671, 0.633649143, 0.64065295,
    0.647580967, 0.65443563, 0.661219252, 0.667934, 0.674581896,
    0.6811649, 0.687684904, 0.69414365, 0.70054287, 0.7068842,
    0.713169109, 0.7193991, 0.725575614, 0.7317, 0.734741009,
    0.7377695, 0.740785594, 0.74378943, 0.746781211, 0.74976104,
    0.752729087, 0.7556855, 0.758630368, 0.76156384, 0.764486065,
    0.76739717, 0.770297266, 0.7731865, 0.776064962, 0.77893275,
    0.781790055, 0.784637, 0.787473608, 0.7903, 0.792803968,
    0.79530001, 0.797800015, 0.8003, 0.802799995, 0.8053,
    0.8078, 0.81029999, 0.812799985, 0.81529999, 0.81779999,
    0.82029999, 0.82279999, 0.82529999, 0.82779999, 0.83029999,
    0.83279999, 0.83529999, 0.83779999, 0.84029999, 0.84279999,
    0.84529999, 0.84779999, 0.85029999, 0.85279999, 0.85529999,
    0.85779999, 0.86029999, 0.86279999, 0.86529999
]
# type chart
typeChart = [
    ["", "Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel", 
     "Fire", "Water", "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark", "Fairy"],
    [1.0,1.0,1.0,1.0,1.0,1.0,0.625,1.0,0.391,0.625,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],
    [1.0,1.6,1.0,0.625,0.625,1.0,1.6,0.625,0.391,1.6,1.0,1.0,1.0,1.0,0.625,1.6,1.0,1.6,0.625],
    [1.0,1.0,1.6,1.0,1.0,1.0,0.625,1.6,1.0,0.625,1.0,1.0,1.6,0.625,1.0,1.0,1.0,1.0,1.0],
    [1.0,1.0,1.0,1.0,0.625,0.625,0.625,1.0,0.625,0.391,1.0,1.0,1.6,1.0,1.0,1.0,1.0,1.0,1.6],
    [1.0,1.0,1.0,0.391,1.6,1.0,1.6,0.625,1.0,1.6,1.6,1.0,0.625,1.6,1.0,1.0,1.0,1.0,1.0],
    [1.0,1.0,0.625,1.6,1.0,0.625,1.0,1.6,1.0,0.625,1.6,1.0,1.0,1.0,1.0,1.6,1.0,1.0,1.0],
    [1.0,1.0,0.625,0.625,0.625,1.0,1.0,1.0,0.625,0.625,0.625,1.0,1.6,1.0,1.6,1.0,1.0,1.6,0.625],
    [1.0,0.391,1.0,1.0,1.0,1.0,1.0,1.0,1.6,1.0,1.0,1.0,1.0,1.0,1.6,1.0,1.0,0.625,1.0],
    [1.0,1.0,1.0,1.0,1.0,1.0,1.6,1.0,1.0,0.625,0.625,0.625,1.0,0.625,1.0,1.6,1.0,1.0,1.6],
    [1.0,1.0,1.0,1.0,1.0,1.0,0.625,1.6,1.0,1.6,0.625,0.625,1.6,1.0,1.0,1.6,0.625,1.0,1.0],
    [1.0,1.0,1.0,1.0,1.0,1.6,1.6,1.0,1.0,1.0,1.6,0.625,0.625,1.0,1.0,1.0,0.625,1.0,1.0],
    [1.0,1.0,1.0,0.625,0.625,1.6,1.6,0.625,1.0,0.625,0.625,1.6,0.625,1.0,1.0,1.0,0.625,1.0,1.0],
    [1.0,1.0,1.0,1.6,1.0,0.391,1.0,1.0,1.0,1.0,1.0,1.6,0.625,0.625,1.0,1.0,0.625,1.0,1.0],
    [1.0,1.0,1.6,1.0,1.6,1.0,1.0,1.0,1.0,0.625,1.0,1.0,1.0,1.0,0.625,1.0,1.0,0.391,1.0],
    [1.0,1.0,1.0,1.6,1.0,1.6,1.0,1.0,1.0,0.625,0.625,0.625,1.6,1.0,1.0,0.625,1.6,1.0,1.0],
    [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,0.625,1.0,1.0,1.0,1.0,1.0,1.0,1.6,1.0,0.391],
    [1.0,1.0,0.625,1.0,1.0,1.0,1.0,1.0,1.6,1.0,1.0,1.0,1.0,1.0,1.6,1.0,1.0,0.625,0.625],
    [1.0,1.0,1.6,1.0,0.625,1.0,1.0,1.0,1.0,0.625,0.625,1.0,1.0,1.0,1.0,1.0,1.6,1.6,1.0]
]
# weather chart
weatherChart = {
    "No" : [],
    "Extreme" : [],
    "Sunny" : [5, 10, 12],
    "Clear" : [5, 10, 12],
    "Rain" : [7, 11, 13],
    "Cloudy" : [2, 4, 18],
    "PartlyCloudy" : [1, 6],
    "Windy" : [3, 14, 16],
    "Snow" : [9, 15],
    "Fog" : [8, 17]
}

#---------------------------------------------------------------------------------#
#-----------------------------Generic Functions-----------------------------------#
#---------------------------------------------------------------------------------#

# remove "_" in a string and convert to lower cases with capitalized first letter 
def toLowerString(upperString:str):
    splitUpperString = upperString.split("_")
    return "".join(shortString.capitalize() for shortString in splitUpperString)

# calculate cp given the base stats and IVs
def cpFormula(pLvl:int, baseAtt:int, baseDef:int, baseSta:int, 
                        attIv:int,   defIv:int,   staIv:int):
    return max(10, int(math.floor((baseAtt+attIv) * 
                                   math.sqrt(baseDef+defIv) * 
                                   math.sqrt(baseSta+staIv) * 
                                  (CPM[pLvl]**2.0) / 10.0)))
#---------------------------------------------------------------------------------#
#-----------------------------------The Bot---------------------------------------#
#---------------------------------------------------------------------------------#    

class Smeargle(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        print("__init__: cog is loading up")
        self.lastRaid = datetime.utcnow()
        self.chanDict = {}
        print("__init__: chanDict is now empty")
        with open(configPath+"PokemonStats.json") as infile:
            self.pokemonStats = json.load(infile)
        with open(configPath+"QuickMoves.json") as infile:
            self.quickMoves = json.load(infile)
        with open(configPath+"ChargeMoves.json") as infile:
            self.chargeMoves = json.load(infile)
        with open(configPath+"SignupMsgs.json") as infile:
            self.roleDict = json.load(infile)
        with open(configPath+"TrainerProfiles.json") as infile:
            self.trainerDict = json.load(infile)
        with open(configPath+"BossSchedule.json") as infile:
            self.bossSchedule = json.load(infile)
        with open(configPath+"IDSettings.json") as infile:
            self.IdSettings = json.load(infile)
        with open(configPath+"GymDictionary.json") as infile:
            self.gymDict = json.load(infile)
        print("__init__: json files loaded")
        print("__init__: finished initialization")
            
#---------------------------------------------------------------------------------#
#---------------------------functions for functions-------------------------------#
#---------------------------------------------------------------------------------#

    # calculate level 20 and 25 cp for 10/10/10 and 15/15/15 ivs
    def calRaidCP(self, pokemonName:str):
        if pokemonName[1:].find("Mega") >= 0:
            # if it's a mega raid, change the name to non-mega form
            loc = pokemonName[1:].find("Mega")
            pokemonName = pokemonName[:loc + 1]
        baseAtt = self.pokemonStats[pokemonName]["att"]
        baseDef = self.pokemonStats[pokemonName]["def"]
        baseSta = self.pokemonStats[pokemonName]["sta"]
        pLvl = 40
        minCP = cpFormula(pLvl, baseAtt, baseDef, baseSta, 10, 10, 10)
        maxCP = cpFormula(pLvl, baseAtt, baseDef, baseSta, 15, 15, 15)
        pLvl = 50
        minCPBoosted = cpFormula(pLvl, baseAtt, baseDef, baseSta, 10, 10, 10)
        maxCPBoosted = cpFormula(pLvl, baseAtt, baseDef, baseSta, 15, 15, 15)
        return minCP, maxCP, minCPBoosted, maxCPBoosted
        
    # return the weaknesses' text of a pokemon
    def calType(self, pokemonName:str):
        type1 = self.pokemonStats[pokemonName]["type"]
        ptypes = [typeChart[0][type1]]
        type2 = self.pokemonStats[pokemonName]["type2"]
        if type2:
            ptypes.append(typeChart[0][type2])
        etypes = []
        for itype in range(18):
            fEff = typeChart[itype+1][type1] * typeChart[itype+1][type2]
            if fEff > 1.01 and fEff <= 2.0:
                etypes.append(typeChart[0][itype+1])
            elif fEff > 2.0:
                etypes.append(typeChart[0][itype+1] + "(x2)")
            
        return ", ".join(etype for etype in etypes)
        
    # initialize a normal group embed message in a raid channel
    # called within createRaid, and can also be created by %group command
    async def createGroupEmbed(self, chanId, checkChan):
        # number of existing group embeds
        numGroup = len(self.chanDict[chanId]["embedTimes"])
        # fill new embed title and sign-up tables
        embedNew = discord.Embed(title="Group " + str(numGroup+1), color=defaultColor)
        embedNew.add_field(name=groupHostText, value=groupNooneText, inline=True)
        embedNew.add_field(name=groupInpersonText, value=groupNooneText, inline=True)
        embedNew.add_field(name=groupRemoteText, value=groupNooneText, inline = True)
        embedNew.add_field(name=instructionText, value=hostEmojiString + ": host (one host per group).\n" +
                                                       inpersonEmojiString + ": join in person.\n" +
                                                       remoteEmojiString + ": join remotely (5 trainers at most).", inline = True)              
        embedMsgTime = await checkChan.send(embed=embedNew)
        await embedMsgTime.pin()
        # add the emoji's for sign-ups
        #emoji = await checkChan.guild.fetch_emoji(hostEmojiId)
        await embedMsgTime.add_reaction(hostEmojiString)
        #emoji = await checkChan.guild.fetch_emoji(inpersonEmojiId)
        await embedMsgTime.add_reaction(inpersonEmojiString)
        #emoji = await checkChan.guild.fetch_emoji(remoteEmojiId)
        await embedMsgTime.add_reaction(remoteEmojiString)
        print("createGroupEmbed: group embed {} for channel {} has been sent".format(str(numGroup+1), checkChan.name))
        # record this embed and initialize the sign-up lists in cache
        self.chanDict[chanId]["embedTimes"].append(embedMsgTime.id)
        self.chanDict[chanId]["signupLists"][embedMsgTime.id] = {}
        
    # initialize an in-person only group embed message in a raid channel
    # called within createRaid, and can also be created by %group command
    async def createInPersonGroupEmbed(self, chanId, checkChan):
        # number of existing group embeds
        numGroup = len(self.chanDict[chanId]["embedTimes"])
        # fill new embed title and sign-up tables
        embedNew = discord.Embed(title="In-person Group " + str(numGroup+1), color=defaultColor)
        embedNew.add_field(name=groupInpersonText, value=groupNooneText, inline=True)
        embedNew.add_field(name=instructionText, value="This is an in-person only group. React with " + inpersonEmojiString + " to indicate you can join in person", inline = True)        
        embedMsgTime = await checkChan.send(embed=embedNew)
        await embedMsgTime.pin()
        # add the emoji's for sign-ups
        #emoji = await checkChan.guild.fetch_emoji(inpersonEmojiId)
        await embedMsgTime.add_reaction(inpersonEmojiString)
        print("createGroupEmbed: group embed {} for channel {} has been sent".format(str(numGroup+1), checkChan.name))
        # record this embed and initialize the sign-up lists in cache
        self.chanDict[chanId]["embedTimes"].append(embedMsgTime.id)
        self.chanDict[chanId]["signupLists"][embedMsgTime.id] = {}
        
    # initialize a raid channel for a new raid, returns the channel id for this raid
    async def createRaid(self, raidType:int, raidName:str, raidTimer:int, gymname:str, submitTime):
        for chanId in raidChanIds:
            checkChan = get(self.bot.get_all_channels(), id=chanId)
            if (checkChan.category.id == warehouseId and self.chanDict[chanId]["status"] == "Warehouse" and 
                datetime.utcnow() > self.chanDict[chanId]["lastCmd"] + timedelta(minutes=chanCooldownMinutes)):
                self.chanDict[chanId]["status"] = "Prep"
                print("createRaid: channel {} is available".format(checkChan.name))
                # convert gym name to channel name
                gymnameNew = gymname
                gymnameNew = gymnameNew.replace(" ", "-")
                gymnameNew = "".join(char for char in gymnameNew if (char.isalnum() or char == "-"))
                # convert Pokemon/raid name to channel name
                raidNameNew = re.sub(r"(?<=\w)([A-Z])", r"-\1", raidName)
                # create channel name
                chanName = raidNameNew + "┃" + gymnameNew
                await checkChan.edit(name=chanName)
                print("createRaid: channel name has been changed to {}".format(chanName))
                # find default raid timer
                if raidType == 1:
                    raidLevel = raidName
                else:
                    raidLevel = self.pokemonStats[raidName]["rLevel"]
                useRaidTimer = raidLevels[raidLevel]["raidTimer"]
                # check if any event would alter the raid timer
                eventName = ""                    
                for schedule in self.bossSchedule["schedules"]:
                    scheduleStartTime = datetime.strptime(schedule["startTime"], timeForm)
                    scheduleEndTime = datetime.strptime(schedule["endTime"], timeForm)
                    if (schedule["type"] == "Event" and
                        "raidTimerOverride" in schedule and
                        submitTime + timedelta(hours=advanceHours) >= scheduleStartTime  and 
                        submitTime + timedelta(hours=backHours) <= scheduleEndTime):
                        print("createRaid: {} is ongoing somewhere in the world".format(eventName))
                        if raidLevel in schedule:
                            eventName = schedule["name"]
                    if (schedule["type"] == "Event" and
                        "raidTimerOverride" in schedule and
                        submitTime + timedelta(hours=timeZoneHours) >= scheduleStartTime and 
                        submitTime + timedelta(hours=timeZoneHours) <= scheduleEndTime):
                        overrideList = schedule["raidTimerOverride"]
                        if (raidType == 1 and raidLevel in overrideList and 
                            submitTime + timedelta(hours=timeZoneHours) + timedelta(minutes=useRaidTimer) >= scheduleStartTime):
                            useRaidTimer = overrideList[raidLevel]
                            print("createRaid: raid timer overriden as {}".format(str(useRaidTimer)))
                        elif raidType == 2 and raidLevel in overrideList:
                            useRaidTimer = overrideList[raidLevel]
                            print("createRaid: raid timer overriden as {}".format(str(useRaidTimer)))
                # purge channel
                await checkChan.purge(limit=100)
                await checkChan.purge(limit=100)
                print("createRaid: channel has been purgued twice")
                # retrieve embed info
                if raidType == 1:
                    imgUrl = raidLevels[raidLevel]["url"]
                    startTime = submitTime + timedelta(hours=timeZoneHours) + timedelta(minutes=raidTimer)
                    endTime = startTime + timedelta(minutes=useRaidTimer)
                    weaknessText = "?"
                    cpText = "Normal: ?-?\nBoosted: ?-?"
                    embedColor = defaultColor
                elif raidType == 2:
                    pokemon = self.pokemonStats[raidName]
                    imgUrl = pokemon["url"]
                    if pokemon["shinyReleased"]:
                        imgUrl = imgPathShiny + imgUrl + ".png"
                    else:
                        imgUrl = imgPath + imgUrl + ".png"
                    endTime = submitTime + timedelta(hours=timeZoneHours) + timedelta(minutes=raidTimer)
                    startTime = endTime - timedelta(minutes=useRaidTimer)
                    weaknessText = self.calType(raidName)
                    cp1, cp2, cp3, cp4 = self.calRaidCP(raidName)
                    cpText = "Normal: " + str(cp1) + "-" + str(cp2) + "\nBoosted: " + str(cp3) + "-" + str(cp4)
                    if raidTimer >= cautionMinutes:
                        embedColor = defaultColor
                    elif raidTimer < urgentMinutes:
                        embedColor = urgentColor
                    else:
                        embedColor = cautionColor
                # create embeds
                embed1 = discord.Embed(title=raidName + " raid at " + gymname, color=embedColor)
                embed2 = discord.Embed(title=raidName + " raid at " + gymname, color=embedColor)
                # thumbnail
                embed1.set_thumbnail(url = imgUrl)
                embed2.set_thumbnail(url = imgUrl)
                # time strings
                startTimeStr = startTime.strftime(timeFormShorter)
                endTimeStr = endTime.strftime(timeFormShorter)
                embed1.add_field(name=activeStartText, value=startTimeStr, inline=True)
                embed1.add_field(name=activeEndText, value=endTimeStr, inline=True)
                startTimeStr = startTime.strftime(timeForm)
                endTimeStr = endTime.strftime(timeForm)
                embed2.add_field(name=activeStartText, value=startTimeStr, inline=True)
                embed2.add_field(name=activeEndText, value=endTimeStr, inline=True)
                # embed1 has channel link and sign-up count
                embed1.add_field(name=activeChannelText, value="<#{}>".format(str(chanId)), inline=True)
                embed1.add_field(name=activeSignupText, value="0", inline=True)
                # embed2 has raid info
                embed2.add_field(name=raidWeaknessText, value=weaknessText, inline=True)
                embed2.add_field(name=raidCPText, value=cpText, inline=True)
                embed2.add_field(name=instructionText, 
                                 value="React to one of the following groups.\n" +
                                       #"<:{}:{}> for in-person\n".format(inpersonEmojiName, str(inpersonEmojiId)) +
                                       #"<:{}:{}> for remote\n".format(remoteEmojiName, str(remoteEmojiId)) +
                                       #"<:{}:{}> if you can host others\n".format(hostEmojiName, str(hostEmojiId)) +
                                       #hostEmojiString + "if you can host others\n" +
                                       #inpersonEmojiString + "for in-person\n" +
                                       #remoteEmojiString + "for remote\n" +
                                       #accountEmoji[0] + accountEmoji[1] + "..." + accountEmoji[-1] + " to indicate how many OTHERS are in your group\n" +
                                       "Use %group to create a new group.\n" +
                                       "Use %buzz to send messages to a group.\n" +
                                       "Use %close to close a group.\n" + 
                                       "Use %update, %gym, %extend to adjust raid Pokemon, gym, and time.", inline=True)
                gymnameShort = gymname.replace(" ", "")
                if gymnameShort in self.gymDict:
                    embed2.add_field(name=mapText, value=self.gymDict[gymnameShort]["map"], inline=True)
                else:
                    embed2.add_field(name=mapText, value="This is not a recorded gym.", inline=True)
                # both embeds need @ roles
                roles = []
                if gymnameShort in self.gymDict:
                    if self.gymDict[gymnameShort]["role2"]:
                        roleName = self.gymDict[gymnameShort]["role1"]
                        role = get(checkChan.guild.roles, name=roleName)
                        roles.append(role)
                if raidType == 1:
                    if "role" in raidLevels[raidLevel]:
                        roleName = raidLevels[raidLevel]["role"]
                        role = get(checkChan.guild.roles, name=roleName)
                        roles.append(role)
                elif raidType == 2:
                    if "role" in raidLevels[raidLevel]:
                        roleName = raidLevels[raidLevel]["role"]
                        role = get(checkChan.guild.roles, name=roleName)
                        roles.append(role)
                    potentialRoleName = "Raid" + raidName
                    role = get(checkChan.guild.roles, name=potentialRoleName)
                    if role:
                        roles.append(role)
                    if self.pokemonStats[raidName]["shinyReleased"]:
                        roleName = raidShinyName
                        role = get(checkChan.guild.roles, name=roleName)
                        roles.append(role)        
                roleContent = " ".join(role.mention for role in roles)
                # embed2 allows mention
                embedMsg2 = await checkChan.send(content=roleContent, embed=embed2, allowed_mentions=discord.AllowedMentions(roles=True))
                await embedMsg2.pin()
                print("createRaid: embed2 has been sent")
                self.chanDict[chanId]["embed2"] = embedMsg2.id
                # the first group message
                self.chanDict[chanId]["embedTimes"] = []
                if raidLevel in inPersonTierNames:
                    await self.createInPersonGroupEmbed(chanId, checkChan)
                else:
                    await self.createGroupEmbed(chanId, checkChan)
                self.chanDict[chanId]["rlevel"] = raidLevel
                # event notification
                if eventName:
                    await checkChan.send("It looks like a {} event is ongoing somewhere in the world.\nPlease use %extend to adjust the end time if it's not accurate due to being an event raid.".format(eventName))
                # move the channel
                raidCategory = get(self.bot.get_all_channels(), id=raidCategoryId)
                await checkChan.edit(category=raidCategory, sync_permissions=True)
                print("createRaid: channel {} has been moved to active raids".format(checkChan.name))
                self.chanDict[chanId]["status"] = "Active"
                # embed1 does not allow mention
                activeChan = get(self.bot.get_all_channels(), id=activeChanId)
                embedMsg1 = await activeChan.send(content=roleContent, embed = embed1)
                print("createRaid: embed1 has been sent")
                self.chanDict[chanId]["embed1"] = embedMsg1.id
                # gym name cache
                self.chanDict[chanId]["gymname"] = gymnameNew
                # log this activity here
                outString = "At " + str(submitTime) + ", a " + raidName + " is created at gym " + gymname + " with " + str(raidTimer) + " minutes left.\n"
                with open(configPath + "BotLog.txt", "a", newline="\n") as outfile:
                    outfile.write(outString)
                # the output is the channel id
                return chanId
                
        return 0
    
    # check the gym name against the channel dictionary to see if it is a duplicate  
    async def findDuplicateChan(self, placeToSend, gymname:str, author, noCtx:bool):
        # keep only letters/numbers from the 2nd gym name
        gymname = gymname.replace(" ", "")
        gymname = "".join(char for char in gymname if char.isalnum())
        # find all 1st gym names that look similar to the 2nd gym name
        checkList = []
        for chanId in self.chanDict:
            if self.chanDict[chanId]["gymname"]:
                name = self.chanDict[chanId]["gymname"]
                name = name.replace("-", "")
                if fuzz.ratio(gymname.lower(), name.lower()) == 100:
                    checkList.append(chanId)
                elif len(name) >= len(gymname) and name.lower()[:len(gymname)] == gymname.lower():
                    checkList.append(chanId)
                elif len(gymname) >= len(name) and gymname.lower()[:len(name)] == name.lower():
                    checkList.append(chanId)
                elif fuzz.ratio(gymname.lower(), name.lower()) > 85:
                    checkList.append(chanId)
        # ask the user if they need to continue creating the raid      
        if checkList:
            outputString = author.mention + " The following gym(s) look similar to this one, if you still want to create this raid, type Y, otherwise, type N:\n"
            outputString += "\n".join("<#{}>".format(chanId) for chanId in checkList)
            await placeToSend.send(outputString)
            def check1(message):
                return message.channel == placeToSend and message.author == author
            def check2(message):
                return message.channel == placeToSend.message.channel and message.author == author
            if noCtx:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                except:
                    await placeToSend.send(errorEmoji + " Timeout.")
                    return True
            else:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check2)
                except:
                    await placeToSend.send(errorEmoji + " Timeout.")
                    return True
            if msg.content.strip().upper() == "Y":
                return False
            else:
                return True
        else:
            return False
        
        return True
        
    # preprocess an input for a name by comparing to keys in a dictionary
    # no special characters in the nameDict entries
    async def handleNames(self, placeToSend, nameInput:str, nameDict:dict, noCtx:bool, author):
        # keep only letters/numbers
        nameInput = "".join(char for char in nameInput if char.isalnum())
        # find all dict keys that look similar
        nameList = []
        for name in nameDict:
            if fuzz.ratio(nameInput.lower(), name.lower()) == 100:
                nameList.append(name)
            elif name.lower()[:len(nameInput)] == nameInput.lower():
                nameList.append(name)
            elif fuzz.partial_ratio(nameInput.lower(), name.lower()) == 100 or \
                 fuzz.ratio(nameInput.lower(), name.lower()) > 85:
                if not noCtx:
                    nameList.append(name)
            elif "mega" in nameInput.lower() and "mega" in name.lower():
                testName = "Mega" + name.lower().replace("mega", "")
                if fuzz.ratio(nameInput.lower(), testName.lower()) == 100:
                    nameList.append(name)
                elif testName.lower()[:len(nameInput)] == nameInput.lower():
                    nameList.append(name)
                elif fuzz.partial_ratio(nameInput.lower(), testName.lower()) == 100 or \
                     fuzz.ratio(nameInput.lower(), testName.lower()) > 85:
                    if not noCtx:
                        nameList.append(name)
        # ask the user to choose the name
        if len(nameList) == 0:
            return ""
        elif len(nameList) == 1:
            return nameList[0]
        else:
            outputString = author.mention + " Please choose a name from the following list. Type a number:\n"
            for index, name in enumerate(nameList):
                outputString += "{}.{} ".format(str(index+1), name)
            outputString += "{}. None of the above".format(str(len(nameList)+1))
            await placeToSend.send(outputString)
            def check1(message):
                return message.channel == placeToSend and message.author == author
            def check2(message):
                return message.channel == placeToSend.message.channel and message.author == author
            if noCtx:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                except:
                    await placeToSend.send(errorEmoji + " Timeout.")
                    return ""
                try:
                    nameNum = int(msg.content) 
                except:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                    return ""
                if nameNum > len(nameList)+1 or nameNum < 1:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                    return ""
                if nameNum > len(nameList):
                    return ""
                return nameList[nameNum-1]
            else:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check2)
                except:
                    await placeToSend.send(errorEmoji + " Timeout.")
                    return ""
                try:
                    nameNum = int(msg.content) 
                except:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                    return ""
                if nameNum > len(nameList)+1 or nameNum < 1:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                    return ""
                if nameNum > len(nameList):
                    return ""
                return nameList[nameNum-1]
            
        return ""
        
    # preprocess an input for a place name by comparing to keys in a dictionary
    # no special characters in the nameDict entries
    async def handlePlaceNames(self, placeToSend, nameInput:str, nameDict:dict, noCtx:bool, author):
        # keep only letters/numbers
        nameInput = "".join(char for char in nameInput if char.isalnum())
        # find all dict keys that look similar
        nameList = []
        for name in nameDict:
            if fuzz.ratio(nameInput.lower(), name.lower()) == 100:
                if len(name) > 10:
                    return name
                else:
                    nameList.append(name)
            elif name.lower()[:len(nameInput)] == nameInput.lower():
                nameList.append(name)
            elif fuzz.ratio(nameInput.lower(), name.lower()) > 85:
                nameList.append(name)
        # ask the user to choose the name
        if len(nameList) == 0:
            return ""
        if len(nameList) == 1 and len(nameList[0]) > 10:
            return nameList[0]
        else:
            outputString = author.mention + " Please choose a gym from the following list. Type a number:\n"
            for index, name in enumerate(nameList):
                outputString += "{}.{} ({}) ".format(str(index+1), name, nameDict[name]["role1"])
            outputString += "{}. None of the above".format(str(len(nameList)+1))
            await placeToSend.send(outputString)
            def check1(message):
                return message.channel == placeToSend and message.author == author
            def check2(message):
                return message.channel == placeToSend.message.channel and message.author == author
            if noCtx:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                except:
                    await placeToSend.send(errorEmoji + " Timeout.")
                    return ""
                try:
                    nameNum = int(msg.content) 
                except:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                    return ""
                if nameNum > len(nameList)+1 or nameNum < 1:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                    return ""
                if nameNum > len(nameList):
                    return ""
                return nameList[nameNum-1]
            else:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check2)
                except:
                    await placeToSend.send(errorEmoji + " Timeout.")
                    return ""
                try:
                    nameNum = int(msg.content) 
                except:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                    return ""
                if nameNum > len(nameList)+1 or nameNum < 1:
                    await placeToSend.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                    return ""
                if nameNum > len(nameList):
                    return ""
                return nameList[nameNum-1]
            
        return ""
        
    # relink all activate raid channels
    # only done when there is no cache
    # should not be called when actually running the bot stably
    async def iniChanDict(self):
        # clear each entry
        for chanId in raidChanIds:
            self.resetChanDict(chanId)
        print("iniChanDict: all chanIds reset")
        # read all messages in the active raid channel
        activeChan = get(self.bot.get_all_channels(), id=activeChanId)
        activeChanCache = {msg.id: msg async for msg in activeChan.history(limit=100)}
        print("iniChanDict: active raid cache now has {} messages".format(len(activeChanCache)))
        # for each message, find the corresponding channel id
        for msgId in activeChanCache:
            activeMsg = await activeChan.fetch_message(msgId)
            if len(activeMsg.embeds) > 0:
                msgEmbed = activeMsg.embeds[0]
                embed_dict = msgEmbed.to_dict()
                raidChanId = 0
                for field in embed_dict["fields"]:
                    if field["name"] == activeChannelText:
                        chanId = int(field["value"][2:-1])
                        embedId1 = msgId
                        if chanId in self.chanDict:
                            self.chanDict[chanId]["embed1"] = embedId1
                        else:
                            print("iniChanDict: channel {} couldn't be found".format(str(chanId)))
        # for each raid channel, check the active status
        for chanId in raidChanIds:
            checkChan = get(self.bot.get_all_channels(), id=chanId)
            if checkChan.category.id == raidCategoryId:
                self.chanDict[chanId]["status"] = "Active"
                # re-cache the gym name
                chanName = checkChan.name
                gymname = chanName.split("┃")[1]
                self.chanDict[chanId]["gymname"] = gymname
                print("iniChanDict: channel {} is still active".format(chanName))
                # check the link with embed1
                if self.chanDict[chanId]["embed1"]:
                    print("iniChanDict: already found the corresponding embed1")
                else:
                    print("iniChanDict: couldn't find the corresponding embed1")
                # read the last 100 messages in the raid channel
                checkChanCache = {msg.id: msg async for msg in checkChan.history(limit=100)}
                # re-cache all the embed2's
                embedId2 = 0
                embedTimes = []
                for msgId in checkChanCache:
                    activeMsg = await checkChan.fetch_message(msgId)
                    if len(activeMsg.embeds) > 0:
                        msgEmbed = activeMsg.embeds[0]
                        embed_dict = msgEmbed.to_dict()
                        for field in embed_dict["fields"]:
                            if field["name"] == activeStartText:
                                embedId2 = msgId
                                print("iniChanDict: found the corresponding top embed")
                                break
                        if embedId2:
                            break
                        elif "Group" in embed_dict["title"]:
                            print("iniChanDict: found a group time embed")
                            embedTimes.append(msgId)
                            self.chanDict[chanId]["signupLists"][msgId] = {}
                            await self.signupRecache(activeMsg, chanId)
                            await self.signupUpdate(activeMsg, chanId)
                            print("iniChanDict: signup states reupdated")
                if embedId2:
                    pass
                else:
                    print("iniChanDict: couldn't find the corresponding embed2")
                self.chanDict[chanId]["embed2"] = embedId2
                if embedTimes:
                    pass
                else:
                    print("iniChanDict: couldn't find the corresponding group times")
                embedTimes.reverse()
                self.chanDict[chanId]["embedTimes"] = embedTimes     
            elif checkChan.category.id == warehouseId:
                self.chanDict[chanId]["status"] = "Warehouse"
                print("iniChanDict: channel {} is in the warehouse".format(checkChan.name))
            self.chanDict[chanId]["lastCmd"] = datetime.utcnow() - timedelta(minutes=(chanCooldownMinutes+1))
            
    # monitor when to hide a raid channel
    # this process can either be started by createRaid, or by a command in a raid channel after bot restart
    async def monitorRaid(self, chanId):
        # the reminder is only sent once
        sentReminder = False
        # the embeds are used to check if the channel status has changed due to reloading/ripping
        orginalEmbed = self.chanDict[chanId]["embed2"]
        activeEmbed = self.chanDict[chanId]["embed1"]
        # link to embed content
        activeChan = get(self.bot.get_all_channels(), id=activeChanId)
        checkChan = get(self.bot.get_all_channels(), id=chanId)
        activeMsg = await checkChan.fetch_message(orginalEmbed)
        msgEmbed = activeMsg.embeds[0]
        embed_dict = msgEmbed.to_dict()
        # use the top embed to determine the end time
        timeStr = ""
        for field in embed_dict["fields"]:
            if field["name"] == activeEndText:
                timeStr = field["value"]
                break
        print("monitorRaid: current end time for channel {} is {}".format(checkChan.name, timeStr))
        try:
            endTime = datetime.strptime(timeStr, timeForm)
        except:
            print('monitorRaid: end time string "{}" for channel {} is not valid, stopping monitor'.format(timeStr, checkChan.name))
            return
        # the "infinite" loop
        while datetime.utcnow() + timedelta(hours=timeZoneHours) < endTime + timedelta(minutes=deleteMinutes):
            await asyncio.sleep(monitorCooldownSeconds)
            # stop if the top embed has changed
            if not self.chanDict[chanId]["embed2"] == orginalEmbed:
                print("monitorRaid: the top embed in channel {} has changed id, stopping monitor".format(checkChan.name))
                return
            # check the end time again, because it could have been edited
            try:
                activeMsg = await checkChan.fetch_message(self.chanDict[chanId]["embed2"])
                msgEmbed = activeMsg.embeds[0]
                embed_dict = msgEmbed.to_dict()
                timeStr = ""
                for field in embed_dict["fields"]:
                    if field["name"] == activeEndText:
                        timeStr = field["value"]
                        break
                endTime = datetime.strptime(timeStr, timeForm)
            except:
                print("monitorRaid: failed to get the end time in channel {}, stopping monitor".format(checkChan.name))
                return
            # stop if the channel has been moved
            if not checkChan.category.id == raidCategoryId:
                print("monitorRaid: channel {} is no longer active, stopping monitor".format(checkChan.name))
                return
            # the check
            print("monitorRaid: checking {}, current end time is {}".format(checkChan.name, timeStr))
            # change embed colors based on time left
            embedColor = defaultColor
            if datetime.utcnow() + timedelta(hours=timeZoneHours) > endTime - timedelta(minutes=cautionMinutes):
                embedColor = cautionColor
            if datetime.utcnow() + timedelta(hours=timeZoneHours) > endTime - timedelta(minutes=urgentMinutes):
                embedColor = urgentColor
            if not embedColor == embed_dict["color"]:
                embed_dict["color"] = embedColor
                newMsgEmbed = discord.Embed.from_dict(embed_dict)
                await activeMsg.edit(embed=newMsgEmbed)
                # another color change for the active channel embed
                activeMsg = await activeChan.fetch_message(activeEmbed)
                msgEmbed = activeMsg.embeds[0]
                embed_dict = msgEmbed.to_dict()
                embed_dict["color"] = embedColor
                newMsgEmbed = discord.Embed.from_dict(embed_dict)
                await activeMsg.edit(embed=newMsgEmbed)
            # send the reminder once
            if datetime.utcnow() + timedelta(hours=timeZoneHours) > endTime - timedelta(seconds=monitorCooldownSeconds) and not sentReminder:
                await checkChan.send(notifEmoji + " This channel will be deactivated in {} minutes. You can use %extend to add more time.".format(str(int(deleteMinutes+monitorCooldownSeconds/60))))
                sentReminder = True
        # clean up the channel and send it back
        self.chanDict[chanId]["status"] = "Cleanup"
        warehouse = get(self.bot.get_all_channels(), id=warehouseId)
        await checkChan.edit(category=warehouse, sync_permissions=True)
        print("monitorRaid: channel {} has been moved to the warehouse".format(checkChan.name))
        activeChan = get(self.bot.get_all_channels(), id=activeChanId)
        try:
            activeMsg = await activeChan.fetch_message(self.chanDict[chanId]["embed1"])
            await activeMsg.delete()
            print("monitorRaid: the embed1 corresponding to channel {} has been deleted".format(checkChan.name))
        except:
            print("monitorRaid: couldn't find the embed1 corresponding to channel {}".format(checkChan.name))
        self.resetChanDict(chanId)
        self.chanDict[chanId]["lastCmd"] = datetime.utcnow()
        # reset channel name
        chanName = "raid-channel-" + str(raidChanIds.index(chanId)+1)
        await checkChan.edit(name=chanName)
        print("monitorRaid: channel name has been changed to {}".format(chanName))
        self.chanDict[chanId]["status"] = "Warehouse"
    
    # use the current dictionary data to overwrite the json files
    # only do this in temporary commands where the pokemon data are intentionally modified
    def overwriteJson(self):
        with open(configPath+"PokemonStats.json", "w") as outfile:
            json.dump(self.pokemonStats, outfile, indent=4)
        with open(configPath+"QuickMoves.json", "w") as outfile:
            json.dump(self.quickMoves, outfile, indent=4)
        with open(configPath+"ChargeMoves.json", "w") as outfile:
            json.dump(self.chargeMoves, outfile, indent=4)
        print("overwriteJson: json files overwritten")
        
    # reset the channel dictionary for a particular channel
    def resetChanDict(self, chanId):
        self.chanDict[chanId] = {}
        self.chanDict[chanId]["gymname"] = ""
        self.chanDict[chanId]["rlevel"] = ""
        self.chanDict[chanId]["embed1"] = 0
        self.chanDict[chanId]["embed2"] = 0
        self.chanDict[chanId]["embedTimes"] = []
        self.chanDict[chanId]["hosts"] = []
        self.chanDict[chanId]["signupLists"] = {}
        self.chanDict[chanId]["lastCmd"] = datetime.utcnow() - timedelta(minutes=(chanCooldownMinutes+1))
    
    # Recache the signup lists, only done if the bot is reloaded
    async def signupRecache(self, messageToUpdate, chanId):
        signupDict = self.chanDict[chanId]["signupLists"][messageToUpdate.id]
        for reaction in messageToUpdate.reactions:
            # it's a reaction for additional trainers
            if isinstance(reaction.emoji, str):
                if reaction.emoji in accountEmoji:
                    users = [user async for user in reaction.users()]
                    numAdd = accountEmoji.index(reaction.emoji) + 1
                    for user in users:
                        if user.bot:
                           continue
                        if not user.id in signupDict:
                            signupDict[user.id] = {}
                        signupDict[user.id]["num"] = numAdd
            # it's a reaction for in-person
            #elif reaction.emoji.name == inpersonEmojiName:
                elif reaction.emoji == inpersonEmojiString:
                    users = [user async for user in reaction.users()]
                    for user in users:
                        if user.bot:
                            continue
                        if not user.id in signupDict:
                            signupDict[user.id] = {}
                        signupDict[user.id]["in-person"] = 1
            # it's a reaction for remote
            #elif reaction.emoji.name == remoteEmojiName:
                elif reaction.emoji == remoteEmojiString:
                    users = [user async for user in reaction.users()]
                    for user in users:
                        if user.bot:
                            continue
                        if not user.id in signupDict:
                            signupDict[user.id] = {}
                        signupDict[user.id]["remote"] = 1
            # it's a reaction for host
            #elif reaction.emoji.name == hostEmojiName:
                elif reaction.emoji == hostEmojiString:
                    users = [user async for user in reaction.users()]
                    for user in users:
                        if user.bot:
                            continue
                        if not user.id in signupDict:
                            signupDict[user.id] = {}
                        signupDict[user.id]["host"] = 1
    
    # Refresh the signup message embed
    async def signupUpdate(self, messageToUpdate, chanId):
        signupDict = self.chanDict[chanId]["signupLists"][messageToUpdate.id]
        # process the cached dictionary
        inpersonEntries = []
        remoteEntries = []
        hostId = 0
        hostCode = "no friend code set, please use %code xxxx xxxx xxxx to input"
        for userId in signupDict:
            signupEntry = "<@{}> ".format(str(userId))
            if "host" in signupDict[userId] and signupDict[userId]["host"]:
                hostId = userId
                if str(userId) in self.trainerDict and "code" in self.trainerDict[str(userId)] and self.trainerDict[str(userId)]["code"]:
                    hostCode = self.trainerDict[str(userId)]["code"]
                else:
                    hostCode = "no friend code set, please use %code xxxx xxxx xxxx to input"
            # if signed up with in-person, it will override remote
            if "in-person" in signupDict[userId] and signupDict[userId]["in-person"]:
                if "num" in signupDict[userId] and signupDict[userId]["num"]:
                    signupEntry += "(+" + str(signupDict[userId]["num"]) + " trainers)"
                inpersonEntries.append(signupEntry)
            elif "remote" in signupDict[userId] and signupDict[userId]["remote"]:
                if "num" in signupDict[userId] and signupDict[userId]["num"]:
                    signupEntry += "(+" + str(signupDict[userId]["num"]) + " trainers)"
                remoteEntries.append(signupEntry)
        # host text
        if hostId:
            hostText = "<@{}> : {}".format(str(hostId), hostCode)
        else:
            hostText = groupNooneText
        # in-person text
        if inpersonEntries:
            inpersonText = "\n".join(signupEntry for signupEntry in inpersonEntries)
        else:
            inpersonText = groupNooneText
        # remote text
        if remoteEntries:
            remoteText = "\n".join(signupEntry for signupEntry in remoteEntries)
        else:
            remoteText = groupNooneText
        # count how many signups for each group, and find the maximum
        maxSignups = 0
        for msgKey in self.chanDict[chanId]["signupLists"]:
            signupMsg = self.chanDict[chanId]["signupLists"][msgKey]
            signupCount = 0
            for userId in signupMsg:
                if "in-person" in signupMsg[userId] and signupMsg[userId]["in-person"]:
                    signupCount += 1
                elif "remote" in signupMsg[userId] and signupMsg[userId]["remote"]:
                    signupCount += 1
                elif "host" in signupMsg[userId] and signupMsg[userId]["host"]:
                    signupCount += 1
            if signupCount > maxSignups:
                maxSignups = signupCount
        # need to check if the new list is the same as the old list
        somethingChanged = False
        msgEmbed = messageToUpdate.embeds[0]
        embed_dict = msgEmbed.to_dict()
        for field in embed_dict["fields"]:
            if field["name"] == groupInpersonText and not field["value"] == inpersonText:
                field["value"] = inpersonText
                somethingChanged = True
            if field["name"] == groupRemoteText and not field["value"] == remoteText:
                field["value"] = remoteText
                somethingChanged = True
            elif field["name"] == groupHostText and not field["value"] == hostText:
                field["value"] = hostText
                somethingChanged = True
        # if the text has changed, update, otherwise skip
        if somethingChanged:
            newMsgEmbed = discord.Embed.from_dict(embed_dict)
            if hostId:
                topText = hostCode
                await messageToUpdate.edit(content=topText, embed=newMsgEmbed)
            else:
                await messageToUpdate.edit(content="", embed=newMsgEmbed)
            activeChan = get(self.bot.get_all_channels(), id=activeChanId)
            try:
                activeMsg = await activeChan.fetch_message(self.chanDict[chanId]["embed1"])
                msgEmbed = activeMsg.embeds[0]
                embed_dict = msgEmbed.to_dict()
                for field in embed_dict["fields"]:
                    if field["name"] == activeSignupText and not field["value"] == str(maxSignups):
                        field["value"] = str(maxSignups)
                        newMsgEmbed = discord.Embed.from_dict(embed_dict)
                        await activeMsg.edit(embed=newMsgEmbed)
                        break
            except:
                print("signupUpdate: couldn't find the embed1 {} in active raids!".format(str(self.chanDict[chanId]["embed1"])))
        else:
            print("signupUpdate: nothing has changed")
            
    # use IdSettings to overwrite the current config file 
    def writeIds(self):
        with open(configPath+"IDSettings.json", "w") as outfile:
            json.dump(self.IdSettings, outfile, indent=4)
        print("writeIds: json file overwritten")
    
    # use gymDict to overwrite the current config file
    def writeGyms(self):
        with open(configPath+"GymDictionary.json", "w") as outfile:
            json.dump(self.gymDict, outfile, indent=4)
        print("writeGyms: json file overwritten")
    
    # use bossSchedule to overwrite the current config file 
    def writeSchedules(self):
        with open(configPath+"BossSchedule.json", "w") as outfile:
            json.dump(self.bossSchedule, outfile, indent=4)
        print("writeSchedules: json file overwritten")
    
    # use roleDict to overwrite the current config file
    # done every time a new signup message is sent    
    def writeSignupMsg(self):
        with open(configPath+"SignupMsgs.json", "w") as outfile:
            json.dump(self.roleDict, outfile, indent=4)
        print("writeSignupMsg: json file overwritten")
        
    # use trainerDict to overwrite the current config file
    # done every time a new trainer code is set    
    def writeTrainerProfiles(self):
        with open(configPath+"TrainerProfiles.json", "w") as outfile:
            json.dump(self.trainerDict, outfile, indent=4)
        print("writeTrainerProfiles: json file overwritten")
        
#---------------------------------------------------------------------------------#
#----------------------------commands for managers--------------------------------#
#---------------------------------------------------------------------------------#  

    # remove 100 messages from a channel and reset channel name
    # can only be done in raid channels when they are in the warehouse
    @commands.command(pass_context=True)
    async def clearc(self, ctx, *args):
        # can only be used by raid managers in raid channels
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id in raidChanIds:
            return
            
        if not self.chanDict:
            await ctx.send(cacheText)
            print("clearc: no cache, rebuilding...")
            await self.iniChanDict()
            
        # can only do this when the channel is in the warehouse
        chanId = ctx.message.channel.id
        checkChan = get(self.bot.get_all_channels(), id=chanId)
        if checkChan.category.id == warehouseId:
            self.chanDict[chanId]["status"] = "Cleanup"
            warehouse = get(self.bot.get_all_channels(), id=warehouseId)
            await ctx.message.channel.purge(limit=100)
            print("clearc: channel {} has been purged".format(checkChan.name))
            self.chanDict[chanId]["status"] = "Warehouse"
        else:
            await ctx.send(notifEmoji + " You can't do this in an active raid channel.")

        return 

    # return an active channel to the warehouse, unlink messages
    # now it uses the monitorRaid impulse to do this
    @commands.command(pass_context=True)
    async def rip(self, ctx, *args):
        # can only be used by raid managers in raid channels
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id in raidChanIds:
            return
            
        if not self.chanDict:
            await ctx.send(cacheText)
            print("rip: no cache, rebuilding...")
            await self.iniChanDict() 
            
        if datetime.utcnow() < self.chanDict[ctx.message.channel.id]["lastCmd"] + timedelta(seconds=raidCooldownSeconds):
            await ctx.message.channel.send(cooldownText)
            return
        self.chanDict[ctx.message.channel.id]["lastCmd"] = datetime.utcnow()
        
        chanId = ctx.message.channel.id
        checkChan = get(self.bot.get_all_channels(), id=chanId)
        if checkChan.category.id == raidCategoryId:
            activeMsg = await ctx.message.channel.fetch_message(self.chanDict[chanId]["embed2"])
            msgEmbed = activeMsg.embeds[0]
            embed_dict = msgEmbed.to_dict()
            timeStr = "01/01/2000 01:00:00 AM"
            endTime = datetime.strptime(timeStr, timeForm)
            for field in embed_dict["fields"]:
                if field["name"] == activeEndText:
                    field["value"] = timeStr
                    break
            # update top embed
            newMsgEmbed = discord.Embed.from_dict(embed_dict)
            await activeMsg.edit(embed=newMsgEmbed)
            print("rip: edited embed2's end time")
            # update active embed
            activeChan = get(self.bot.get_all_channels(), id=activeChanId)
            activeMsg = await activeChan.fetch_message(self.chanDict[ctx.message.channel.id]["embed1"])
            msgEmbed = activeMsg.embeds[0]
            embed_dict = msgEmbed.to_dict()
            for field in embed_dict["fields"]:
                if field["name"] == activeEndText:
                    field["value"] = endTime.strftime(timeFormShorter)
                    break
            newMsgEmbed = discord.Embed.from_dict(embed_dict)
            await activeMsg.edit(embed=newMsgEmbed)
            print("rip: edited embed1's end time")
            await ctx.send(okayEmoji + " This channel will be removed soon. No need to use this command again.")
        else:
            await ctx.send(notifEmoji + " This channel is not an active raid channel.")
    
        return
        
    # reset and return all raid channels to warehouse
    # only do this when debugging the bot
    # normal channel edits should be handled differently
    @commands.command(pass_context=True)
    async def ripall(self, ctx, *args):
        # can only be used by raid managers in debug channel
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id == debugChanId:
            return
            
        warehouse = get(self.bot.get_all_channels(), id=warehouseId)
        
        for index, chanId in enumerate(raidChanIds):
            checkChan = get(self.bot.get_all_channels(), id=chanId)
            if not checkChan.category.id == warehouseId:
                await checkChan.edit(category=warehouse, sync_permissions=True)
                print("iniChanDict: channel {} has been moved to the warehouse".format(checkChan.name))
            await checkChan.purge(limit=100)
            print("iniChanDict: channel {} has been purged".format(checkChan.name))
            
        activeChan = get(self.bot.get_all_channels(), id=activeChanId)
        await activeChan.purge(limit=100)
        print("iniChanDict: channel {} has been purged".format(activeChan.name))
        
        for chanId in raidChanIds:
            self.resetChanDict(chanId)
            self.chanDict[chanId]["status"] = "Warehouse"
            
        await ctx.send(okayEmoji + " All raid channels have been reset.")
    
        return
        
    # change the release state of a pokemon
    @commands.command(name="release",
                      description="E.g., %release bulbasaur.",
                      pass_context=True)
    async def release(self, ctx, pokemonNameInput:str):
        # can only be used by raid managers in debug channel
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id == debugChanId:
            return
            
        try:
            pokemonName = await self.handleNames(ctx, pokemonNameInput, self.pokemonStats, False, ctx.message.author)
            if not pokemonName:
                await ctx.send(errorEmoji + ' Failed to find "{}" as a recorded Pokemon name.'.format(pokemonNameInput))
                return
        except:
            await ctx.send(errorEmoji + ' Failed to process "{}" as a Pokemon name.'.format(pokemonNameInput))            
            return
            
        print("release: pokemon name read as {}".format(pokemonName))
        
        if self.pokemonStats[pokemonName]["released"] == 1:
            oldState = "Released"
            newState = "Unreleased"
            self.pokemonStats[pokemonName]["released"] = 0
        else:
            oldState = "Unreleased"
            newState = "Released"
            self.pokemonStats[pokemonName]["released"] = 1
        self.overwriteJson()
        
        await ctx.send(okayEmoji + " Changed {} from {} to {}!".format(pokemonName, oldState, newState))
        print("release: changed {} from {} to {}!".format(pokemonName, oldState, newState))
        
        return
        
    # change the raid level of a pokemon
    @commands.command(name="rlevel",
                      description="E.g., %rlevel bulbasaur supermega.",
                      pass_context=True)
    async def rlevel(self, ctx, pokemonNameInput:str, rLevelInput:str):
        # can only be used by raid managers in debug channel
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id == debugChanId:
            return
            
        try:
            pokemonName = await self.handleNames(ctx, pokemonNameInput, self.pokemonStats, False, ctx.message.author)
            if not pokemonName:
                await ctx.send(errorEmoji + ' Failed to find "{}" as a recorded Pokemon name.'.format(pokemonNameInput))
                return
        except:
            await ctx.send(errorEmoji + ' Failed to process "{}" as a Pokemon name.'.format(pokemonNameInput))            
            return
            
        print("rlevel: pokemon name read as {}".format(pokemonName))
        
        try:
            rLevel = await self.handleNames(ctx, rLevelInput, raidLevels, False, ctx.message.author)
            if not rLevel:
                await ctx.send(errorEmoji + " Failed to find {} as a recorded raid level.".format(rLevelInput))
                return
        except:
            await ctx.send(errorEmoji + " Failed to process {} as a raid level.".format(rLevelInput))            
            return
            
        print("rlevel: raid level read as {}".format(rLevel))
        
        oldLevel = str(self.pokemonStats[pokemonName]["rLevel"])
        self.pokemonStats[pokemonName]["rLevel"] = rLevel
        self.overwriteJson()
        
        await ctx.send(okayEmoji + " Changed {}'s raid level from {} to {}!".format(pokemonName, oldLevel, rLevel))
        print("rlevel: changed {}'s raid level from {} to {}".format(pokemonName, oldLevel, rLevel))
        
        return
    
    # change the shiny release state of a pokemon
    @commands.command(name="srelease",
                      description="E.g., %srelease bulbasaur.",
                      pass_context=True)
    async def srelease(self, ctx, pokemonNameInput:str):
        # can only be used by raid managers in debug channel
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id == debugChanId:
            return
            
        try:
            pokemonName = await self.handleNames(ctx, pokemonNameInput, self.pokemonStats, False, ctx.message.author)
            if not pokemonName:
                await ctx.send(errorEmoji + ' Failed to find "{}" as a recorded Pokemon name.'.format(pokemonNameInput))
                return
        except:
            await ctx.send(errorEmoji + ' Failed to process "{}" as a Pokemon name.'.format(pokemonNameInput))            
            return
            
        print("srelease: pokemon name read as {}".format(pokemonName))
        
        if self.pokemonStats[pokemonName]["shinyReleased"] == 1:
            oldState = "Released"
            newState = "Unreleased"
            self.pokemonStats[pokemonName]["shinyReleased"] = 0
        else:
            oldState = "Unreleased"
            newState = "Released"
            self.pokemonStats[pokemonName]["shinyReleased"] = 1
        self.overwriteJson()
        
        await ctx.send(okayEmoji + " Changed {}'s raid shiny status from {} to {}!".format(pokemonName, oldState, newState))
        print("srelease: changed {}'s raid shiny status from {} to {}!".format(pokemonName, oldState, newState))
        
        return
        
    # display all available info of a pokemon using an embed
    @commands.command(name="stats",
                      description="E.g., %stats bulbasaur.",
                      pass_context=True)
    async def stats(self, ctx, pokemonNameInput:str):
        # can only be used by raid managers in debug channel
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id == debugChanId:
            return     
        
        try:
            pokemonName = await self.handleNames(ctx, pokemonNameInput, self.pokemonStats, False, ctx.message.author)
            if not pokemonName:
                await ctx.send(errorEmoji + ' Failed to find "{}" as a recorded Pokemon name.'.format(pokemonNameInput))
                return
        except:
            await ctx.send(errorEmoji + ' Failed to process "{}" as a Pokemon name.'.format(pokemonNameInput))            
            return
            
        print("stats: pokemon name read as {}".format(pokemonName))
        
        pokemon = self.pokemonStats[pokemonName]
        embed = discord.Embed(title=pokemonName, color=defaultColor)
        imgUrl = pokemon["url"]
        imgUrl = imgPath + imgUrl + r".png"
        embed.set_thumbnail(url=imgUrl)
        embed.add_field(name="Base Stats", value=str(pokemon["att"])+"/"+str(pokemon["def"])+"/"+str(pokemon["sta"]), inline=True)
        typeString = typeChart[0][pokemon["type"]]
        if pokemon["type2"]:
            typeString += "/" + typeChart[0][pokemon["type2"]]
        embed.add_field(name="Type", value=typeString, inline=True)
        if pokemon["quickMoves"]:
            embed.add_field(name="Quick Moves",  value=", ".join([qmove for qmove in pokemon["quickMoves"]]), inline=True)
        if pokemon["chargeMoves"]:
            embed.add_field(name="Charge Moves", value=", ".join([cmove for cmove in pokemon["chargeMoves"]]), inline=True)
        embed.add_field(name="Raid Level", value=pokemon["rLevel"], inline=True)
        if pokemon["released"]:
            embed.add_field(name="Released", value="Yes", inline=True)
        else:
            embed.add_field(name="Released", value="No", inline=True)
        if pokemon["shinyReleased"]:
            embed.add_field(name="Raid Shiny", value="Yes", inline=True)
        else:
            embed.add_field(name="Raid Shiny", value="No", inline=True)
        await ctx.send(embed=embed)
        
        print("stats: pokemon embed sent")
        
        return
        
    # go through the current boss schedule and update the signup roles/messages if necessary
    @commands.command(pass_context=True)
    async def updateBosses(self, ctx):
        # can only be used by raid managers in debug channel
        if not ctx.message.author.id in self.IdSettings["managerIds"] or not ctx.message.channel.id == debugChanId:
            return
            
        if not self.chanDict:
            await ctx.send(cacheText)
            print("updateBosses: no cache, rebuilding...")
            await self.iniChanDict()
            
        currentTime = datetime.utcnow() + timedelta(hours=timeZoneHours)
        
        currentStartTime = datetime.strptime(self.bossSchedule["current"]["startTime"], timeForm)
        
        # check if there are any schedules that should have started by now
        # if default, find the latest one that should have started, and remove the rest
        # if event, find the latest one that should have started and not ended, and remove the rest
        latestDefaultSchedule = -1
        latestDefaultStartTime = currentStartTime
        latestEventSchedule = -1
        latestEventStartTime = currentStartTime
        newSchedules = []
        for index, schedule in enumerate(self.bossSchedule["schedules"]):
            if schedule["type"] == "Default":
                startTime = datetime.strptime(schedule["startTime"], timeForm)
                if startTime < currentTime:
                    if startTime > latestDefaultStartTime:
                        latestDefaultStartTime = startTime
                        latestDefaultSchedule = index
                else:
                    newSchedules.append(schedule.copy())
            elif schedule["type"] == "Event":
                startTime = datetime.strptime(schedule["startTime"], timeForm)
                endTime = datetime.strptime(schedule["endTime"], timeForm)
                if startTime < currentTime:
                    if endTime > currentTime and startTime > latestEventStartTime:
                        latestEventStartTime = startTime
                        latestEventSchedule = index
                else:
                    newSchedules.append(schedule.copy())
                        
        if latestDefaultSchedule >= 0:
            print("updateBosses: new default schedule found")
            self.bossSchedule["last"] = self.bossSchedule["current"].copy()
            self.bossSchedule["current"] = self.bossSchedule["schedules"][latestDefaultSchedule].copy()
        
        if latestEventSchedule >= 0:
            print("updateBosses: new event schedule found")
        
        self.bossSchedule["schedules"] = newSchedules
        self.writeSchedules()
        
        guild = ctx.message.guild
        
        # update the signup messages using the schedules
        # Level5 and Mega should include any last and next schedule ongoing somewhere in the world
        # while the others should only include local ongoing ones
        pokemonToInclude = {}
        for tierName in tierNamesShort:
            pokemonToInclude[tierName] = []
        roleUpdateTiers = ["Level5", "Mega"]
        
        schedule = self.bossSchedule["last"]
        if (datetime.strptime(schedule["endTime"], timeForm) - 
            timedelta(hours=backHours) > datetime.utcnow() + timedelta(hours=timeZoneHours)):
            for tierName in roleUpdateTiers:
                if tierName in schedule:
                    for roleName in schedule[tierName]:
                        if not roleName in pokemonToInclude[tierName]:
                            pokemonToInclude[tierName].append(roleName)
        for schedule in self.bossSchedule["schedules"]:
            if (schedule["type"] == "Default" and
                datetime.strptime(schedule["startTime"], timeForm) -
                timedelta(hours=advanceHours) < datetime.utcnow() + timedelta(hours=timeZoneHours)):
                for tierName in roleUpdateTiers:
                    if tierName in schedule:
                        for roleName in schedule[tierName]:
                            if not roleName in pokemonToInclude[tierName]:
                                pokemonToInclude[tierName].append(roleName)
        for schedule in self.bossSchedule["schedules"]:
            if (schedule["type"] == "Event" and
                datetime.strptime(schedule["startTime"], timeForm) -
                timedelta(hours=advanceHours) < datetime.utcnow() + timedelta(hours=timeZoneHours) and
                datetime.strptime(schedule["endTime"], timeForm) -
                timedelta(hours=backHours) > datetime.utcnow() + timedelta(hours=timeZoneHours)):
                for tierName in tierNamesShort:
                    if tierName in schedule:
                        for roleName in schedule[tierName]:
                            if not roleName in pokemonToInclude[tierName]:
                                pokemonToInclude[tierName].append(roleName)
        schedule = self.bossSchedule["current"]
        for tierName in tierNamesShort:
            if tierName in schedule:
                for roleName in schedule[tierName]:
                    if not roleName in pokemonToInclude[tierName]:
                        pokemonToInclude[tierName].append(roleName)
                        
        # update pokemon data with the above info
        for tierName in tierNamesShort:
            for pokemonName in pokemonToInclude[tierName]:
                self.pokemonStats[pokemonName]["rLevel"] = tierName
        self.overwriteJson()
        
        # update sign-up messages        
        singupChan = get(self.bot.get_all_channels(), id=signupChanId)
        for tierName in tierNamesShort:
            signupText = ""
            pIndex = 0
            for msgId in self.roleDict:
                # find the tier in SignupMsgs.json
                if self.roleDict[msgId]["type"] == tierName:
                    activeMsg = await singupChan.fetch_message(int(msgId))
                    # check if there are enough roles assigned to this tier
                    numRoles = len(self.roleDict[msgId]["roles"])
                    numPokemon = len(pokemonToInclude[tierName])
                    if numPokemon > numRoles:
                        print("updateBosses: not all scheduled Pokemon in {} can fit into the roles".format(tierName))
                    for index in range(numRoles):
                        # if the old role still exists in the new list, skip
                        oldRoleName = self.roleDict[msgId]["roles"][index]
                        oldPokemonName = oldRoleName.replace("Raid", "")
                        if oldPokemonName in pokemonToInclude[tierName]:
                            signupText += accountEmoji[index] + " " + oldPokemonName + "\n"
                            continue
                        # else, check if there is a new role to put here
                        if index < numPokemon:
                            newRoleName = "Raid" + pokemonToInclude[tierName][pIndex]
                            skipThis = False
                            while newRoleName in self.roleDict[msgId]["roles"]:
                                pIndex += 1
                                if pIndex == len(pokemonToInclude[tierName]):
                                    skipThis = True
                                    break
                                newRoleName = "Raid" + pokemonToInclude[tierName][pIndex]
                            if skipThis:
                                signupText += accountEmoji[index] + " " + oldPokemonName + "\n"
                                continue
                            signupText += accountEmoji[index] + " " + pokemonToInclude[tierName][pIndex] + "\n"
                        else:
                            newRoleName = "Raid" + tierName + "P" + str(index+1)
                        # if a new role will be put in here, remove old role
                        if not oldRoleName == newRoleName:
                            role = get(guild.roles, name=oldRoleName)
                            if role:
                                # need to remove the old role from everyone with it
                                # also need to remove all non-bot reactions for the old role
                                for member in role.members:
                                    print("updateBosses: removing role {} from member {}".format(role.name, member.name))
                                    await member.remove_roles(role)
                                    for reaction in activeMsg.reactions:
                                        if isinstance(reaction.emoji, str):
                                            if reaction.emoji in accountEmoji:
                                                if accountEmoji.index(reaction.emoji) == index:
                                                    await reaction.remove(member)
                                # apply the new role name
                                await role.edit(name=newRoleName)
                            self.roleDict[msgId]["roles"][index] = newRoleName
                            print("updateBosses: role {} has been renamed to {}".format(oldRoleName, newRoleName))
                    # change the corresponding embed
                    msgEmbed = activeMsg.embeds[0]
                    embed_dict = msgEmbed.to_dict()
                    for field in embed_dict["fields"]:
                        if field["name"] == instructionText:
                            if signupText:
                                field["value"] = signupText
                            else:
                                field["value"] = "No {} bosses right now".format(tierName)
                    newMsgEmbed = discord.Embed.from_dict(embed_dict)
                    await activeMsg.edit(embed=newMsgEmbed)
                    break
        # overwrite the SignupMsg.json
        self.writeSignupMsg()
        await ctx.send(okayEmoji + " Current raid roles updated. Please double check if everything is correct.")        
        return                  
            
#---------------------------------------------------------------------------------#
#----------------------------commands for everyone--------------------------------#
#---------------------------------------------------------------------------------#    

    # add a gym
    @commands.command(name="addgym",
                      description="E.g., %addgym Downtown 41.82551353486267, -71.41213789341057 Random Gym Name",
                      pass_context=True)
    async def addgym(self, ctx, roleName:str, lati:str, longi:str, *args):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in allChanIds and not ctx.message.channel.id == debugChanId:
            return
        
        if not self.chanDict:
            await ctx.send(cacheText)
            print("addgym: no cache, rebuilding...")
            await self.iniChanDict()
         
        if len(args) < 1:
            await ctx.send(errorEmoji + " There is no gym name provided.")
            return
            
        if not roleName in regionIds:
            await ctx.send(errorEmoji + ' {} is not an available region.'.format(roleName))
            return
            
        lati = lati.replace(",", "")
        lati = lati.replace("(", "")
        longi = longi.replace(",", "")
        longi = longi.replace(")", "")
        
        try:
            lati = float(lati)
        except:
            await ctx.send(errorEmoji + ' {} is not a real number.'.format(str(lati)))
            return
            
        try:
            longi = float(longi)
        except:
            await ctx.send(errorEmoji + ' {} is not a real number.'.format(str(longi)))
            return
        
        googleLink = r"https://www.google.com/maps?q=" + str(lati) + "," + str(longi)
        
        gymname = " ".join(word for word in args)
        gymnameShort = "".join(word for word in args)
        
        if gymnameShort in self.gymDict:
            await ctx.send(errorEmoji + "Gym {} already exists.".format(gymname))
            return
        
        outstring = ' Creating gym "{}" in region "{}". Here is the Google Maps link: {}\nType "Y" to continue, "N" to cancel'.format(gymname, roleName, googleLink)
        await ctx.send(ctx.message.author.mention + outstring)
        
        def check(message):
            return message.channel == ctx.message.channel and message.author == ctx.message.author
        try:
            msg = await self.bot.wait_for("message", timeout=timeoutSeconds*2, check=check)
        except:
            await ctx.send(errorEmoji + " Timeout.")
            return
            
        if msg.content.strip().upper() == "N":
            await ctx.send(notifEmoji + " Gym creation cancelled.")
            return
        elif msg.content.strip().upper() == "Y":
            self.gymDict[gymnameShort] = {}
            self.gymDict[gymnameShort]["name"] = gymname
            self.gymDict[gymnameShort]["role1"] = roleName
            if regionIds[roleName]["parent"]:
                self.gymDict[gymnameShort]["role2"] = regionIds[roleName]["parent"]
            else:
                self.gymDict[gymnameShort]["role2"] = ""
            self.gymDict[gymnameShort]["map"] = googleLink
            await ctx.send(okayEmoji + ' Gym "{}" has been created.'.format(gymname))
            self.writeGyms()
            return
        else:
            await ctx.send(errorEmoji + ' Failed to understand the answer "{}".'.format(msg.content))

        return
    
    # ping a group time
    @commands.command(name="buzz",
                      description="E.g., %buzz 1 going in.",
                      pass_context=True)
    async def buzz(self, ctx, *args):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in raidChanIds:
            return
        if not ctx.message.channel.category.id == raidCategoryId:
            await ctx.send(notifEmoji + " You can only do this in an active raid channel.")
            return
        
        if not self.chanDict:
            await ctx.send(cacheText)
            print("update: no cache, rebuilding...")
            await self.iniChanDict()
            
        if datetime.utcnow() < self.chanDict[ctx.message.channel.id]["lastCmd"] + timedelta(seconds=raidCooldownSeconds):
            await ctx.message.channel.send(cooldownText)
            return
        self.chanDict[ctx.message.channel.id]["lastCmd"] = datetime.utcnow()
        
        for iNum in range(len(self.chanDict[ctx.message.channel.id]["embedTimes"])):
            if not self.chanDict[ctx.message.channel.id]["embedTimes"][iNum] == 0:
                break
        
        # process the group number and text to send
        if len(args) > 0:
            try:
                groupNum = int(args[0])
                if groupNum > len(self.chanDict[ctx.message.channel.id]["embedTimes"]) or groupNum < 1 or self.chanDict[ctx.message.channel.id]["embedTimes"][groupNum-1] == 0:
                    groupNum = iNum
                    pingText = " ".join(word for word in args)
                elif len(args) > 1:
                    groupNum -= 1                
                    pingText = " ".join(word for word in args[1:])
                else:
                    groupNum -= 1
                    pingText = ""
            except:
                groupNum = iNum
                pingText = " ".join(word for word in args)
        else:
            groupNum = iNum
            pingText = ""
        # find the corresponding group embed    
        checkChan = get(self.bot.get_all_channels(), id=ctx.message.channel.id)    
        messageToRead = await checkChan.fetch_message(self.chanDict[ctx.message.channel.id]["embedTimes"][groupNum])
        # find all the users to @
        msgEmbed = messageToRead.embeds[0]
        embed_dict = msgEmbed.to_dict()
        all_text = ""
        for field in embed_dict["fields"]:
            if field["name"] == groupInpersonText:
                if not field["value"] == groupNooneText:
                    inpersonText = field["value"]
                    inpersonText = inpersonText.split("\n")
                    for text in inpersonText:
                        if not str(ctx.message.author.id) in text:
                            all_text += text.split(" ")[0]
            if field["name"] == groupRemoteText:
                if not field["value"] == groupNooneText:
                    remoteText = field["value"]
                    remoteText = remoteText.split("\n")
                    for text in remoteText:
                        if not str(ctx.message.author.id) in text:
                            all_text += text.split(" ")[0]
            elif field["name"] == groupHostText:
                if not field["value"] == groupNooneText:
                    hostText = field["value"]
                    hostText = hostText.split("\n")
                    for text in hostText:
                        if not str(ctx.message.author.id) in text:
                            all_text += text.split(" ")[0]
        # send the text
        if all_text:
            if pingText:
                await ctx.send(all_text+"\n<@{}> says : {}".format(str(ctx.message.author.id), pingText))
            else:
                await ctx.send(all_text+"\n<@{}> pinged you.".format(str(ctx.message.author.id)))
        
        #await ctx.message.delete()
        
        return
        
    # close a raid group
    @commands.command(name="close",
                      description="E.g., %close.",
                      pass_context=True)
    async def close(self, ctx, *args):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in raidChanIds:
            return
        if not ctx.message.channel.category.id == raidCategoryId:
            await ctx.send(notifEmoji + " You can only do this in an active raid channel.")
            return
            
        if not self.chanDict:
            await ctx.send(cacheText)
            print("close: no cache, rebuilding...")
            await self.iniChanDict()
            
        if datetime.utcnow() < self.chanDict[ctx.message.channel.id]["lastCmd"] + timedelta(seconds=raidCooldownSeconds):
            await ctx.message.channel.send(cooldownText)
            return
        self.chanDict[ctx.message.channel.id]["lastCmd"] = datetime.utcnow()
        
        # find the group with the user as host
        chanId = ctx.message.channel.id
        checkChan = get(self.bot.get_all_channels(), id=chanId)
        authorId = ctx.message.author.id
        totalGroups = len(self.chanDict[chanId]["embedTimes"])
        for messageId in self.chanDict[chanId]["signupLists"]:
            if messageId in self.chanDict[chanId]["embedTimes"] and authorId in self.chanDict[chanId]["signupLists"][messageId]:
                if "host" in self.chanDict[chanId]["signupLists"][messageId][authorId] and self.chanDict[chanId]["signupLists"][messageId][authorId]["host"]:
                    activeMsg = await ctx.message.channel.fetch_message(messageId)
                    await activeMsg.delete()
                    print("close: group embed deleted")
                    totalGroups -= 1
                    groupNum = self.chanDict[chanId]["embedTimes"].index(messageId)
                    self.chanDict[chanId]["embedTimes"] = self.chanDict[chanId]["embedTimes"][:groupNum] + [0] + self.chanDict[chanId]["embedTimes"][groupNum+1:]
                    print("close: message id set to 0 in embedTimes")
                    # log this activity here
                    outString = "At " + str(datetime.utcnow() + timedelta(hours=timeZoneHours)) + ", user " + ctx.message.author.name + " closed a raid group.\n"
                    with open(configPath + "BotLog.txt", "a", newline="\n") as outfile:
                        outfile.write(outString)
        
        if totalGroups == 0:
            if self.chanDict[chanId]["rlevel"] in inPersonTierNames:
                await self.createInPersonGroupEmbed(chanId, checkChan)
            else:
                await self.createGroupEmbed(chanId, checkChan)
        
                
        return
        
    # input or update trainer code
    @commands.command(name="code",
                      description="E.g., %code 1234 5678 9999.",
                      pass_context=True)
    async def code(self, ctx, *args):
        if ctx.guild and not ctx.message.channel.id in allChanIds:
            return
        # could be numbers separated by spaces
        msg = " ".join(arg for arg in args)
        try:
            trainerCode = int(msg.strip().replace(" ", ""))
        except:
            await ctx.send(errorEmoji + ' Failed to convert the code "{}" to numbers. Please use %code command to try again.'.format(msg))
            return
        # process the code and record it    
        stringCode = str(trainerCode)
        if not len(stringCode) == 12:
            await ctx.send(errorEmoji + ' The code "{}" needs to have exactly 12 digits. Please use %code command to try again.'.format(stringCode))
            return
        else:
            newCode = stringCode[0:4] + " " + stringCode[4:8] + " " + stringCode[8:12]
            if not str(ctx.message.author.id) in self.trainerDict:
                self.trainerDict[str(ctx.message.author.id)] = {}
            self.trainerDict[str(ctx.message.author.id)]["code"] = newCode
            await ctx.send(okayEmoji + " Your trainer code has been set to: " + stringCode)
            self.writeTrainerProfiles()
            return
            
        return

    #extend the time of the raid channel
    @commands.command(name="extend",
                      description="E.g., %extend 10.",
                      pass_context=True)
    async def extend(self, ctx, addTimer:int):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in raidChanIds:
            return
        if not ctx.message.channel.category.id == raidCategoryId:
            await ctx.send(notifEmoji + " You can only do this in an active raid channel.")
            return
        
        if not self.chanDict:
            await ctx.send(cacheText)
            print("extend: no cache, rebuilding...")
            await self.iniChanDict()
            
        if datetime.utcnow() < self.chanDict[ctx.message.channel.id]["lastCmd"] + timedelta(seconds=raidCooldownSeconds):
            await ctx.message.channel.send(cooldownText)
            return
        self.chanDict[ctx.message.channel.id]["lastCmd"] = datetime.utcnow()
        # obtain the current end time, then add the timer
        activeMsg = await ctx.message.channel.fetch_message(self.chanDict[ctx.message.channel.id]["embed2"])
        msgEmbed = activeMsg.embeds[0]
        embed_dict = msgEmbed.to_dict()
        timeStr = ""
        for field in embed_dict["fields"]:
            if field["name"] == activeEndText:
                timeStr = field["value"]
                endTime = datetime.strptime(timeStr, timeForm)
                endTime += timedelta(minutes=addTimer)
                field["value"] = endTime.strftime(timeForm)
                break
        # update top embed
        newMsgEmbed = discord.Embed.from_dict(embed_dict)
        await activeMsg.edit(embed=newMsgEmbed)
        print("extend: edited embed2's end time")
        # update active embed
        activeChan = get(self.bot.get_all_channels(), id=activeChanId)
        activeMsg = await activeChan.fetch_message(self.chanDict[ctx.message.channel.id]["embed1"])
        msgEmbed = activeMsg.embeds[0]
        embed_dict = msgEmbed.to_dict()
        for field in embed_dict["fields"]:
            if field["name"] == activeEndText:
                timeStrShort = endTime.strftime(timeFormShorter)
                field["value"] = timeStrShort
                break
        newMsgEmbed = discord.Embed.from_dict(embed_dict)
        await activeMsg.edit(embed=newMsgEmbed)
        print("extend: edited embed1's end time")
        
        await ctx.send(okayEmoji + " This channel has been extended by {} minutes. The end time is now {}.".format(addTimer, timeStrShort))
        
        return
        
    # add another raid group to an active raid channel
    @commands.command(name="group",
                      description="E.g., %group.",
                      pass_context=True)
    async def group(self, ctx):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in raidChanIds:
            return
        if not ctx.message.channel.category.id == raidCategoryId:
            await ctx.send(notifEmoji + " You can only do this in an active raid channel.")
            return
        
        if not self.chanDict:
            await ctx.send(cacheText)
            print("update: no cache, rebuilding...")
            await self.iniChanDict()
            
        if datetime.utcnow() < self.chanDict[ctx.message.channel.id]["lastCmd"] + timedelta(seconds=raidCooldownSeconds):
            await ctx.message.channel.send(cooldownText)
            return
        self.chanDict[ctx.message.channel.id]["lastCmd"] = datetime.utcnow()
        # create embed based on raid level
        checkChan = get(self.bot.get_all_channels(), id=ctx.message.channel.id)
        if self.chanDict[ctx.message.channel.id]["rlevel"] in inPersonTierNames:
            await self.createInPersonGroupEmbed(ctx.message.channel.id, checkChan)
        else:
            await self.createGroupEmbed(ctx.message.channel.id, checkChan)
        
        #await ctx.send(okayEmoji + " Group {} has been created.".format(str(len(self.chanDict[ctx.message.channel.id]["embedTimes"]))))
        
        #await ctx.message.delete()
        
        return
        
    # update the name of the raid boss
    @commands.command(name="gym",
                      description="E.g., %gym new gym name.",
                      pass_context=True)
    async def gym(self, ctx, *args):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in raidChanIds:
            return
        if not ctx.message.channel.category.id == raidCategoryId:
            await ctx.send(notifEmoji + " You can only do this in an active raid channel.")
            return
        
        if not self.chanDict:
            await ctx.send(cacheText)
            print("gym: no cache, rebuilding...")
            await self.iniChanDict()
            
        if datetime.utcnow() < self.chanDict[ctx.message.channel.id]["lastCmd"] + timedelta(seconds=raidCooldownSeconds):
            await ctx.message.channel.send(cooldownText)
            return
        self.chanDict[ctx.message.channel.id]["lastCmd"] = datetime.utcnow()
        # process the gym name
        gymname = " ".join(arg for arg in args)
        gymnameOrig = gymname
        gymnameNew = await self.handlePlaceNames(ctx, gymname, self.gymDict, False, ctx.message.author)
        if gymnameNew:
            gymname = self.gymDict[gymnameNew]["name"]
            gymnameOrig = gymname
        gymname = gymname.strip().replace(" ", "-")
        gymname = "".join(char for char in gymname if (char.isalnum() or char == "-"))
        if not gymname:
            await ctx.send(errorEmoji + ' The gym name "{}" does not have any letters'.format(gymnameOrig))
            return
        # update channel name
        chanName = ctx.message.channel.name
        chanName = chanName.split("┃")
        chanName = chanName[0] + "┃" + gymname
        await ctx.message.channel.edit(name=chanName)
        self.chanDict[ctx.message.channel.id]["gymname"] = gymname
        print("gym: channel name has been changed to {}".format(chanName))
        # edit top embed 
        activeMsg = await ctx.message.channel.fetch_message(self.chanDict[ctx.message.channel.id]["embed2"])
        newTexts = ""
        oldContent = activeMsg.content
        print("gym: original mentions: " + oldContent)
        for roleId in roleIds:
            if isinstance(roleIds[roleId], int) and str(roleIds[roleId]) in oldContent:
                newTexts += "<@&{}>".format(str(roleIds[roleId]))
        if gymnameNew:
            if self.gymDict[gymnameNew]["role2"]:
                roleName = self.gymDict[gymnameNew]["role1"]
                role = get(ctx.message.channel.guild.roles, name=roleName)
                if not role.mention in oldContent:
                    newTexts += role.mention
        
        msgEmbed = activeMsg.embeds[0]
        embed_dict = msgEmbed.to_dict()
        oldTitle = embed_dict["title"]
        partitioned_strings = oldTitle.split(" ")[:3]
        partitioned_string = " ".join(word for word in partitioned_strings)
        embed_dict["title"] = partitioned_string + " " + gymnameOrig
        if gymnameNew:
            for field in embed_dict["fields"]:
                if field["name"] == mapText:
                    field["value"] = self.gymDict[gymnameNew]["map"]
        newMsgEmbed = discord.Embed.from_dict(embed_dict)
        await activeMsg.edit(content=newTexts, embed=newMsgEmbed)
        print("gym: edited embed2")
        # edit active embed 
        activeChan = get(self.bot.get_all_channels(), id=activeChanId)
        activeMsg = await activeChan.fetch_message(self.chanDict[ctx.message.channel.id]["embed1"])
        msgEmbed = activeMsg.embeds[0]
        embed_dict = msgEmbed.to_dict()
        embed_dict["title"] = partitioned_string + " " + gymnameOrig
        newMsgEmbed = discord.Embed.from_dict(embed_dict)
        await activeMsg.edit(content=newTexts, embed=newMsgEmbed)
        print("gym: edited embed1")

        await ctx.send(okayEmoji + ' Gym name has been changed to "{}".'.format(gymname))
        
        return

    # manually add raid sightings
    @commands.command(name="raid",
                      description="E.g., %raid, or %raid 1 Level5 30 TestGym, or %raid 2 Mewtwo 30 Test Gym.",
                      pass_context=True)
    async def raid(self, ctx, *args):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in allChanIds:
            return
        if not ctx.message.channel.id == sightingChanId:
            await ctx.send(notifEmoji + " You can only do this in <#{}>.".format(str(sightingChanId)))
            return
            
        if not self.chanDict:
            await ctx.send(cacheText)
            print("raid: no cache, rebuilding...")
            await self.iniChanDict()
            
        checktime = datetime.utcnow()
        polltime = self.lastRaid + timedelta(seconds=raidCooldownSeconds)
        if checktime < polltime:
            await ctx.send(cooldownText)
            return
        self.lastRaid = datetime.utcnow()
        submitTime = datetime.utcnow()
        
        def check(message):
            return message.channel == ctx.message.channel and message.author == ctx.message.author
        
        if len(args) < 1:
            nErrors = 0
            await ctx.send(ctx.message.author.mention + " You are taking the long road to create a raid! You will need to answer several questions.\n" + 
                           "Question 1: has the raid started yet? (Y/N)")
            while nErrors < 3:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check)
                except:
                    await ctx.send(errorEmoji + " Timeout.")
                    return
                if msg.content.strip().upper() == "N":
                    raidType = 1
                    break
                elif msg.content.strip().upper() == "Y":
                    raidType = 2
                    break
                else:
                    nErrors += 1
                    if nErrors == 3:
                        await ctx.send(errorEmoji + ' Failed to understand the answer "{}". Too many tries. Exiting.'.format(msg.content))
                        return
                    else:
                        await ctx.send(notifEmoji + ' Failed to understand the answer "{}". Please type your answer again.'.format(msg.content))
                        continue
            print("raid: manual input raidType = {}".format(str(raidType)))            
            nErrors = 0
            if raidType == 1:
                await ctx.send(ctx.message.author.mention + " So the raid hasn't started. Question 2: how many MINUTES are left on the timer? Type ONE number:")
            elif raidType == 2:
                await ctx.send(ctx.message.author.mention + " So the raid has started. Question 2: how many MINUTES are left on the timer? Type ONE number:")
            while nErrors < 3:
                try:
                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check)
                except:
                    await ctx.send(errorEmoji + " Timeout.")
                    return
                try:
                    raidTimer = int(msg.content)
                except:
                    nErrors += 1
                    if nErrors == 3:
                        await ctx.send(errorEmoji + ' Answer "{}" is not a number. Too many tries. Exiting.'.format(msg.content))
                        return
                    else:
                        await ctx.send(notifEmoji + ' Answer "{}" is not a number. Please type your answer again.'.format(msg.content))
                        continue
                else:
                    break
            if raidType == 2 and raidTimer < urgentMinutes:
                await ctx.send(errorEmoji + r" Sorry, there is too little time (<{} minutes) left on this raid. The raid will not be created.".format(str(urgentMinutes)))
                return
            submitTime = datetime.utcnow()
            print("raid: manual input raidTimer = {}".format(str(raidTimer)))
            nErrors = 0
            if raidType == 1:
                outputString = ctx.message.author.mention + " So the timer left is {}. Question 3: what's the raid type? Choose one by typing a number:\n".format(str(raidTimer))
                for index, name in enumerate(raidLevels):
                    outputString += "{}.{} ".format(str(index + 1), name)
                await ctx.send(outputString)
                while nErrors < 3:
                    try:
                        msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check)
                    except:
                        await ctx.send(errorEmoji + " Timeout.")
                        return
                    try:
                        nameNum = int(msg.content) 
                    except:
                        nErrors += 1
                        if nErrors == 3:
                            await ctx.send(errorEmoji + ' Answer "{}" is not a number. Too many tries. Exiting.'.format(msg.content))
                            return
                        else:
                            await ctx.send(notifEmoji + ' Answer "{}" is not a number. Please type your answer again.'.format(msg.content))
                            continue
                    if nameNum > len(raidLevels) or nameNum < 1:
                        nErrors += 1
                        if nErrors == 3:
                            await ctx.send(errorEmoji + ' Answer "{}" is out of range. Too many tries. Exiting.'.format(msg.content))
                            return
                        else:
                            await ctx.send(notifEmoji + ' Answer "{}" is out of range. Please type your answer again.'.format(msg.content))
                            continue
                    else:
                        raidName = list(raidLevels.keys())[nameNum - 1]
                        break
            else:
                await ctx.send(ctx.message.author.mention + " So the timer left is {}. Question 3: what's the Pokemon name? Type the name:".format(str(raidTimer)))
                while nErrors < 3:
                    try:
                        msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check)
                    except:
                        await ctx.send(errorEmoji + " Timeout.")
                        return
                    nameInput = "".join(char for char in msg.content if char.isalnum())
                    nameList = []
                    for name in self.pokemonStats:
                        displayName = self.pokemonStats[name]["name"]
                        if fuzz.ratio(nameInput.lower(), name.lower()) == 100:
                            nameList.append(name)
                        elif name.lower()[:len(nameInput)] == nameInput.lower():
                            nameList.append(name)
                        elif fuzz.partial_ratio(nameInput.lower(), name.lower()) == 100 or \
                             fuzz.ratio(nameInput.lower(), name.lower()) > 85:
                            nameList.append(name)
                        elif "mega" in nameInput.lower() and "mega" in name.lower():
                            testName = "Mega" + name.lower().replace("mega", "")
                            if fuzz.ratio(nameInput.lower(), testName.lower()) == 100:
                                nameList.append(name)
                            elif testName.lower()[:len(nameInput)] == nameInput.lower():
                                nameList.append(name)
                            elif fuzz.partial_ratio(nameInput.lower(), testName.lower()) == 100 or \
                                fuzz.ratio(nameInput.lower(), testName.lower()) > 85:
                                nameList.append(name)
                    if not nameList:
                        nErrors += 1
                        if nErrors == 3:
                            await ctx.send(errorEmoji + ' Failed to find Pokemon "{}". Too many tries. Exiting.'.format(msg.content))
                            return
                        else:
                            await ctx.send(notifEmoji + ' Failed to find Pokemon "{}". Please type again.'.format(msg.content))
                            continue
                    elif len(nameList) == 1:
                        raidName = nameList[0]
                        break
                    else:
                        outputString = "Choose what you are looking for. Type a number:\n"
                        for index, name in enumerate(nameList):
                            outputString += "{}.{} ".format(str(index + 1), name)
                        await ctx.send(outputString)
                        try:
                            msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check)
                        except:
                            await ctx.send(errorEmoji + " Timeout.")
                            return
                        try:
                            nameNum = int(msg.content) 
                        except:
                            nErrors += 1
                            if nErrors == 3:
                                await ctx.send(errorEmoji + ' Answer "{}" is not a number. Too many tries. Exiting.'.format(msg.content))
                                return
                            else:
                                await ctx.send(notifEmoji + ' Answer "{}" is not a number. Please type a more exact Pokemon name.'.format(msg.content))
                                continue
                        if nameNum > len(nameList) or nameNum < 1:
                            nErrors += 1
                            if nErrors == 3:
                                await ctx.send(errorEmoji + ' Answer "{}" is out of range. Too many tries. Exiting.'.format(msg.content))
                                return
                            else:
                                await ctx.send(notifEmoji + ' Answer "{}" is out of range. Please type a more exact Pokemon name.'.format(msg.content))
                                continue
                        else:
                            raidName = nameList[nameNum - 1]
                            break
            print("raid: manual input raidName = {}".format(raidName))
            await ctx.send(ctx.message.author.mention + " So the raid is {}. Final question: what's the gym name?\n".format(raidName) + 
                "Type as much of the name as you are ok with. It will be used to distiguish this raid from other entries.")
            try:
                msg = await self.bot.wait_for("message", timeout=timeoutSeconds)
            except:
                await ctx.send(errorEmoji + " Timeout.")
                return
            gymname = msg.content
            print("raid: manual input gymname = {}".format(gymname))
        else:
            # preprocess all arguments provided
            if len(args) < 3:
                await ctx.send(errorEmoji + " Not enough input. You need to provide:\n" + 
                               "Raid level/Pokemon name,\n" +
                               "Countdown timer (minutes),\n" +
                               "Gym name.")
                return
            try:
                raidTimer = int(args[1])
            except:
                await ctx.send(errorEmoji + ' Countdown timer remaining "{}" needs to be a single number indicating minutes.\n'.format(args[1]))
                return
            submitTime = datetime.utcnow()
            print("raid: quick input raidTimer = {}".format(str(raidTimer)))
            raidNameInput = args[0]
            if raidNameInput in raidLevels:
                raidType = 1
                raidName = raidNameInput
            elif raidNameInput.capitalize() in raidLevels:
                raidType = 1
                raidName = raidNameInput.capitalize()
            else:
                raidType = 2
                raidName = await self.handleNames(ctx, raidNameInput, self.pokemonStats, False, ctx.message.author)
                if not raidName:
                    await ctx.send(errorEmoji + ' Failed to find "{}" as a recorded raid level or Pokemon name.'.format(raidNameInput))
                    return
            print("raid: quick input raidName = {}".format(raidName))
            gymname = " ".join(word for word in args[2:])
            print("raid: quick input gymname = {}".format(gymname))
            
            if raidType == 2 and raidTimer < urgentMinutes:
                await ctx.send(errorEmoji + r" Sorry, there is too little time (<{} minutes) left on this raid. The raid will not be created.".format(str(urgentMinutes)))
                return
            
        gymname = gymname.strip()
        isDupe = await self.findDuplicateChan(ctx, gymname, ctx.message.author, False)
        if not isDupe:
            gymnameNew = await self.handlePlaceNames(ctx, gymname, self.gymDict, False, ctx.message.author)
            if not gymnameNew:
                gymnameNew = gymname
            else:
                gymnameNew = self.gymDict[gymnameNew]["name"]
        
            channelId = await self.createRaid(raidType, raidName, raidTimer, gymnameNew, submitTime)
            
            if channelId:
                await ctx.send(okayEmoji + " Raid created, please head to <#{}> for raid coordination!".format(str(channelId)))
                await self.monitorRaid(channelId)
                return
            else:
                await ctx.send(errorEmoji + " Failed to find available raid channel. Please ask <@{}> for help.\n".format(str(lucaId)))
                return
        else:
            await ctx.send(notifEmoji + " Raid creation cancelled.\n")
            return
        
        return
        
    # update the name of the raid boss
    @commands.command(name="update",
                      description="E.g., %update bulbasaur.",
                      pass_context=True)
    async def update(self, ctx, *args):
        if not ctx.guild:
            return
        if not ctx.message.channel.id in raidChanIds:
            return
        if not ctx.message.channel.category.id == raidCategoryId:
            await ctx.send(notifEmoji + " You can only do this in an active raid channel.")
            return
        
        if not self.chanDict:
            await ctx.send(cacheText)
            print("update: no cache, rebuilding...")
            await self.iniChanDict()
            
        if datetime.utcnow() < self.chanDict[ctx.message.channel.id]["lastCmd"] + timedelta(seconds=raidCooldownSeconds):
            await ctx.message.channel.send(cooldownText)
            return
        self.chanDict[ctx.message.channel.id]["lastCmd"] = datetime.utcnow()
        
        pokemonNameInput = "".join(word for word in args)       
            
        try:
            pokemonName = await self.handleNames(ctx, pokemonNameInput, self.pokemonStats, False, ctx.message.author)
            if not pokemonName:
                await ctx.send(errorEmoji + ' Failed to find "{}" as a recorded Pokemon name.'.format(pokemonNameInput))
                return
        except:
            await ctx.send(errorEmoji + ' Failed to process "{}" as a Pokemon name.'.format(pokemonNameInput))            
            return
            
        print("update: pokemon name read as {}".format(pokemonName))
            
        pokemon = self.pokemonStats[pokemonName]
        imgUrl = pokemon["url"]
        if pokemon["shinyReleased"]:
            imgUrl = imgPathShiny + imgUrl + ".png"
        else:
            imgUrl = imgPath + imgUrl + ".png"
            
        weaknessText = self.calType(pokemonName)
        cp1, cp2, cp3, cp4 = self.calRaidCP(pokemonName)
        cpText = "Normal: " + str(cp1) + "-" + str(cp2) + "\nBoosted: " + str(cp3) + "-" + str(cp4)

        activeMsg = await ctx.message.channel.fetch_message(self.chanDict[ctx.message.channel.id]["embed2"])
        msgEmbed = activeMsg.embeds[0]
        embed_dict = msgEmbed.to_dict()
        
        oldTitle = embed_dict["title"]
        partitioned_string = oldTitle.partition(" ")[0]
        pokemonNameNew = re.sub(r"(?<=\w)([A-Z])", r"-\1", pokemonName)
        embed_dict["title"] = oldTitle.replace(partitioned_string, pokemonNameNew, 1)
        
        embed_dict["thumbnail"]["url"] = imgUrl
        
        for field in embed_dict["fields"]:
            if field["name"] == raidWeaknessText:
                field["value"] = weaknessText
            elif field["name"] == raidCPText:
                field["value"] = cpText
        
        newMsgEmbed = discord.Embed.from_dict(embed_dict)
        
        oldContent = activeMsg.content
        print("update: original mentions: " + oldContent)
        newTexts = ""
        for roleId in roleIds:
            if isinstance(roleIds[roleId], int) and str(roleIds[roleId]) in oldContent:
                newTexts += "<@&{}>".format(str(roleIds[roleId]))
        addMentions = ""
        if pokemon["shinyReleased"]:
            role = get(ctx.guild.roles, name=raidShinyName)
            newTexts += " " + role.mention
            if not role.mention in oldContent:
                addMentions += " " + role.mention
        potentialRoleName = "Raid" + pokemonName
        role = get(ctx.guild.roles, name=potentialRoleName)
        if role:
            newTexts += " " + role.mention
            if not role.mention in oldContent:
                addMentions += " " + role.mention
        
        await activeMsg.edit(content=newTexts, embed=newMsgEmbed)
        
        print("update: edited embed2")
        
        chanName = ctx.message.channel.name
        chanName = chanName.split("┃")
        chanName = pokemonNameNew + "┃" + chanName[1]
        await ctx.message.channel.edit(name=chanName)
        print("update: channel name has been changed to {}".format(chanName))
        
        activeChan = get(self.bot.get_all_channels(), id=activeChanId)
        activeMsg = await activeChan.fetch_message(self.chanDict[ctx.message.channel.id]["embed1"])
        msgEmbed = activeMsg.embeds[0]
        embed_dict = msgEmbed.to_dict()
        
        oldTitle = embed_dict["title"]
        partitioned_string = oldTitle.partition(" ")[0]
        embed_dict["title"] = oldTitle.replace(partitioned_string, pokemonNameNew, 1)
        
        embed_dict["thumbnail"]["url"] = imgUrl
        
        newMsgEmbed = discord.Embed.from_dict(embed_dict)
        await activeMsg.edit(content=newTexts, embed=newMsgEmbed)
        
        print("update: edited embed1")
        
        await ctx.send(okayEmoji + " Raid boss has been changed to {}.{}".format(pokemonName, addMentions), allowed_mentions=discord.AllowedMentions(roles=True))
        
        return  
        
#---------------------------------------------------------------------------------#
#------------------------------commands for luca----------------------------------#
#---------------------------------------------------------------------------------#  

    # add an id to one of the id list
    @commands.command(pass_context=True)
    async def addId(self, ctx, idToAdd:int, listName:str):
        # can only be used by LucaLucaBea
        if not ctx.message.author.id == lucaId:
            return
            
        self.IdSettings[listName].append(idToAdd)
        
        self.writeIds()
        
        return

    # translate the game master file to a json file
    # for safety reasons, need to manually replace the original json with the generated file
    @commands.command(pass_context=True)
    async def gmaster(self, ctx):
        # can only be used by LucaLucaBea
        if not ctx.message.author.id == lucaId:
            return
        await ctx.send(notifEmoji + " Starting to process GAME_MASTER.json...")
        with open(GMPath) as gameMasterFile:
            gameMaster = json.load(gameMasterFile)
        outString = "there are a total of {} templates in GAME_MASTER.\n".format(str(len(gameMaster)))
        # dictionaries
        PokemonStats = {}
        QuickMoves = {}
        ChargeMoves = {}
        smeargleQuickMoves = []
        smeargleChargeMoves = []
        # go through all entries in the file
        for template in gameMaster:
            if "combatMove" in template["data"]:
                # read PvP move stats
                # templateId COMBAT_V0000_MOVE_EXAMPLE_MOVE
                moveStats = template["data"]["combatMove"]
                moveName = moveStats["uniqueId"]
                print("reading pvp move: " + moveName)
                outString += "pvp move: " + moveName + "\n"
                moveType = typeDict[moveStats["type"]]
                keywords = template["templateId"].split("_")
                moveNum = int(keywords[1][1:])
                if keywords[-1] == "FAST":
                    # this is a quick move
                    if not moveName in QuickMoves:
                        QuickMoves[moveName] = {}
                    QuickMoves[moveName]["num"] = moveNum
                    QuickMoves[moveName]["name"] = toLowerString(moveName[:-5])
                    QuickMoves[moveName]["type"] = moveType
                    try:
                        QuickMoves[moveName]["pvpPower"] = int(moveStats["power"])
                    except:
                        QuickMoves[moveName]["pvpPower"] = 0
                    try:
                        QuickMoves[moveName]["pvpEnergy"] = int(moveStats["energyDelta"])
                    except:
                        QuickMoves[moveName]["pvpEnergy"] = 0
                    try:
                        QuickMoves[moveName]["pvpTurns"] = int(moveStats["durationTurns"]) + 1
                    except:
                        QuickMoves[moveName]["pvpTurns"] = 1
                    # regard hidden power as 18 different moves
                    if moveName == "HIDDEN_POWER_FAST":
                        QuickMoves[moveName]["name"] = "HiddenPowerNormal"
                        for typeName in typeDict:
                            if not typeName == "POKEMON_TYPE_NORMAL":
                                moveType = typeDict[typeName]
                                typeNameShort = typeName[13:].capitalize()
                                moveNameNew = "HIDDEN_POWER_" + typeName[13:] + "_FAST"
                                if not moveNameNew in QuickMoves:
                                    QuickMoves[moveNameNew] = {}
                                QuickMoves[moveNameNew] = QuickMoves[moveName].copy()
                                QuickMoves[moveNameNew]["name"] = "HiddenPower" + typeNameShort
                                QuickMoves[moveNameNew]["type"] = moveType
                                outString += "pvp move: " + moveNameNew + "\n"
                else:
                    # this is a charge move
                    if not moveName in ChargeMoves:
                        ChargeMoves[moveName] = {}
                    ChargeMoves[moveName]["num"] = moveNum
                    ChargeMoves[moveName]["name"] = toLowerString(moveName)
                    ChargeMoves[moveName]["type"] = moveType
                    try:
                        ChargeMoves[moveName]["pvpPower"] = int(moveStats["power"])
                    except:
                        ChargeMoves[moveName]["pvpPower"] = 0
                    try:
                        ChargeMoves[moveName]["pvpEnergy"] = -int(moveStats["energyDelta"])
                    except:
                        ChargeMoves[moveName]["pvpEnergy"] = 50
                    ChargeMoves[moveName]["buffChance"] = 0.0
                    ChargeMoves[moveName]["aaBuff"] = 0
                    ChargeMoves[moveName]["adBuff"] = 0
                    ChargeMoves[moveName]["daBuff"] = 0
                    ChargeMoves[moveName]["ddBuff"] = 0
                    if "buffs" in moveStats:
                        # charge move has stat change effects
                        ChargeMoves[moveName]["buffChance"] = float(moveStats["buffs"]["buffActivationChance"])
                        if "attackerAttackStatStageChange" in moveStats["buffs"]:
                            ChargeMoves[moveName]["aaBuff"] = int(moveStats["buffs"]["attackerAttackStatStageChange"])
                        if "attackerDefenseStatStageChange" in moveStats["buffs"]:
                            ChargeMoves[moveName]["adBuff"] = int(moveStats["buffs"]["attackerDefenseStatStageChange"])
                        if "targetAttackStatStageChange" in moveStats["buffs"]:
                            ChargeMoves[moveName]["daBuff"] = int(moveStats["buffs"]["targetAttackStatStageChange"])
                        if "targetDefenseStatStageChange" in moveStats["buffs"]:
                            ChargeMoves[moveName]["ddBuff"] = int(moveStats["buffs"]["targetDefenseStatStageChange"])
            elif "pokemonSettings" in template["data"]:
                # read Pokemon stats
                # templateId V0000_POKEMON_EXAMPLE_FORM
                pTemp = template["data"]["pokemonSettings"]
                pName = pTemp["pokemonId"]
                if pName in PokemonStats:
                    # check if this is a unique form
                    isUnique = False
                    if PokemonStats[pName]["type"] != typeDict[pTemp["type"]] \
                      or (PokemonStats[pName]["type2"] != 0 and not "type2" in pTemp) \
                      or ("type2" in pTemp and PokemonStats[pName]["type2"] != typeDict[pTemp["type2"]]):
                        # check if pokemon types match
                        isUnique = True
                    if "stats" in pTemp and (PokemonStats[pName]["att"] != int(pTemp["stats"]["baseAttack"]) 
                                          or PokemonStats[pName]["def"] != int(pTemp["stats"]["baseDefense"]) 
                                          or PokemonStats[pName]["sta"] != int(pTemp["stats"]["baseStamina"])):
                        # check if stats match
                        isUnique = True
                    if isUnique:
                        # unique -> read new name
                        pName = pTemp["form"]
                        PokemonStats[pName] = {}
                        print("reading new form: " + pName)
                        outString += "new form: " + pName + "\n"
                    else:
                        #----------outdated--------- not unique -> add any additional moves and skip the rest
                        # not unique -> add any additional moves and skip the rest
                        # check if the name needs an overwrite
                        if pTemp["form"] in overwriteNames:
                            PokemonStats[pName]["name"] = toLowerString(pTemp["form"])
                            print("this form name will overwrite the default name: " + pTemp["form"])
                            outString += "overwrite form: " + pTemp["form"] + "\n"
                        else:
                            print("this is not a unique form: " + pTemp["form"])
                            outString += "duplicate form: " + pTemp["form"] + "\n"
                        if "quickMoves" in pTemp:
                            for moveName in pTemp["quickMoves"]:
                                if moveName == "STRUGGLE":
                                    moveName = "TACKLE_FAST"
                                if not moveName in PokemonStats[pName]["quickMoves"]:
                                    PokemonStats[pName]["quickMoves"].append(moveName)
                                    # handle hidden power
                                    if moveName == "HIDDEN_POWER_FAST":
                                        for typeName in typeDict:
                                            if not typeName == "POKEMON_TYPE_NORMAL":
                                                typeNameShort = typeName[13:].capitalize()
                                                moveNameNew = "HIDDEN_POWER_" + typeName[13:] + "_FAST"
                                                PokemonStats[pName]["quickMoves"].append(moveNameNew)
                        if "cinematicMoves" in pTemp:
                            for moveName in pTemp["cinematicMoves"]:
                                if not moveName in PokemonStats[pName]["chargeMoves"]:
                                    PokemonStats[pName]["chargeMoves"].append(moveName)
                        if "eliteQuickMove" in pTemp:
                            for moveName in pTemp["eliteQuickMove"]:
                                if moveName == "STRUGGLE":
                                    moveName = "TACKLE_FAST"
                                if not moveName in PokemonStats[pName]["quickMoves"]:
                                    PokemonStats[pName]["quickMoves"].append(moveName)
                                    # handle hidden power
                                    if moveName == "HIDDEN_POWER_FAST":
                                        for typeName in typeDict:
                                            if not typeName == "POKEMON_TYPE_NORMAL":
                                                typeNameShort = typeName[13:].capitalize()
                                                moveNameNew = "HIDDEN_POWER_" + typeName[13:] + "_FAST"
                                                PokemonStats[pName]["quickMoves"].append(moveNameNew)
                        if "eliteCinematicMove" in pTemp:
                            for moveName in pTemp["eliteCinematicMove"]:
                                if not moveName in PokemonStats[pName]["chargeMoves"]:
                                    PokemonStats[pName]["chargeMoves"].append(moveName)
                        continue
                else:
                    PokemonStats[pName] = {}
                    print("reading new pokemon: " + pName)
                    outString += "new pokemon: " + pName + "\n"
                keywords = template["templateId"].split("_")
                pNum = int(keywords[0][1:])
                PokemonStats[pName]["num"] = pNum
                PokemonStats[pName]["name"] = toLowerString(pName)
                PokemonStats[pName]["type"] = typeDict[pTemp["type"]]
                if "type2" in pTemp:
                    PokemonStats[pName]["type2"] = typeDict[pTemp["type2"]]
                else:
                    PokemonStats[pName]["type2"] = 0
                PokemonStats[pName]["att"] = 0
                PokemonStats[pName]["def"] = 0
                PokemonStats[pName]["sta"] = 0
                if "stats" in pTemp:
                    try:
                        PokemonStats[pName]["att"] = int(pTemp["stats"]["baseAttack"])
                        PokemonStats[pName]["def"] = int(pTemp["stats"]["baseDefense"])
                        PokemonStats[pName]["sta"] = int(pTemp["stats"]["baseStamina"])
                    except:
                        pass
                PokemonStats[pName]["quickMoves"] = []
                if "quickMoves" in pTemp:
                    for moveName in pTemp["quickMoves"]:
                        if moveName == "STRUGGLE":
                            moveName = "TACKLE_FAST"
                        if not moveName in PokemonStats[pName]["quickMoves"]:
                            PokemonStats[pName]["quickMoves"].append(moveName)
                            # handle hidden power
                            if moveName == "HIDDEN_POWER_FAST":
                                for typeName in typeDict:
                                    if not typeName == "POKEMON_TYPE_NORMAL":
                                        typeNameShort = typeName[13:].capitalize()
                                        moveNameNew = "HIDDEN_POWER_" + typeName[13:] + "_FAST"
                                        PokemonStats[pName]["quickMoves"].append(moveNameNew)
                PokemonStats[pName]["chargeMoves"] = []
                if "cinematicMoves" in pTemp:
                    for moveName in pTemp["cinematicMoves"]:
                        if not moveName in PokemonStats[pName]["chargeMoves"]:
                            PokemonStats[pName]["chargeMoves"].append(moveName)
                if "eliteQuickMove" in pTemp:
                    for moveName in pTemp["eliteQuickMove"]:
                        if moveName == "STRUGGLE":
                            moveName = "TACKLE_FAST"
                        if not moveName in PokemonStats[pName]["quickMoves"]:
                            PokemonStats[pName]["quickMoves"].append(moveName)
                            # handle hidden power
                            if moveName == "HIDDEN_POWER_FAST":
                                for typeName in typeDict:
                                    if not typeName == "POKEMON_TYPE_NORMAL":
                                        typeNameShort = typeName[13:].capitalize()
                                        moveNameNew = "HIDDEN_POWER_" + typeName[13:] + "_FAST"
                                        PokemonStats[pName]["quickMoves"].append(moveNameNew)
                if "eliteCinematicMove" in pTemp:
                    for moveName in pTemp["eliteCinematicMove"]:
                        if not moveName in PokemonStats[pName]["chargeMoves"]:
                            PokemonStats[pName]["chargeMoves"].append(moveName)
                if "tempEvoOverrides" in pTemp:
                    for pEvolveForm in pTemp["tempEvoOverrides"]:
                        if "tempEvoId" in pEvolveForm:
                            # mega evolution
                            pNameNew = pName + pEvolveForm["tempEvoId"][14:]
                            if not pNameNew in PokemonStats:
                                PokemonStats[pNameNew] = {}
                                PokemonStats[pNameNew]["num"] = pNum
                                PokemonStats[pNameNew]["name"] = toLowerString(pNameNew)
                                PokemonStats[pNameNew]["type"] = typeDict[pEvolveForm["typeOverride1"]]
                                if "typeOverride2" in pEvolveForm:
                                    PokemonStats[pNameNew]["type2"] = typeDict[pEvolveForm["typeOverride2"]]
                                else:
                                    PokemonStats[pNameNew]["type2"] = 0
                                PokemonStats[pNameNew]["att"] = pEvolveForm["stats"]["baseAttack"]
                                PokemonStats[pNameNew]["def"] = pEvolveForm["stats"]["baseDefense"]
                                PokemonStats[pNameNew]["sta"] = pEvolveForm["stats"]["baseStamina"]
                                PokemonStats[pNameNew]["quickMoves"] = PokemonStats[pName]["quickMoves"]
                                PokemonStats[pNameNew]["chargeMoves"] = PokemonStats[pName]["chargeMoves"]
            elif "moveSettings" in template["data"]:
                # read PvE move stats
                # templateId V0000_MOVE_EXAMPLE_MOVE
                moveStats = template["data"]["moveSettings"]
                moveName = moveStats["movementId"]
                print("reading pve move " + moveName)
                outString += "pve move: " + moveName + "\n"
                moveType = typeDict[moveStats["pokemonType"]]
                keywords = template["templateId"].split("_")
                moveNum = int(keywords[0][1:])
                if keywords[-1] == "FAST":
                    # this is a quick move
                    if not moveName in QuickMoves:
                        QuickMoves[moveName] = {}
                    QuickMoves[moveName]["num"] = moveNum
                    QuickMoves[moveName]["name"] = toLowerString(moveName[:-5])
                    QuickMoves[moveName]["type"] = moveType
                    try:
                        QuickMoves[moveName]["duration"] = int(moveStats["durationMs"]/10)
                    except:
                        QuickMoves[moveName]["duration"] = 100
                    try:
                        QuickMoves[moveName]["power"] = int(moveStats["power"])
                    except:
                        QuickMoves[moveName]["power"] = 0
                    try:
                        QuickMoves[moveName]["energyDelta"] = int(moveStats["energyDelta"])
                    except:
                        QuickMoves[moveName]["energyDelta"] = 0
                    try:
                        QuickMoves[moveName]["dmgWindow"] = int(moveStats["damageWindowStartMs"]/10)
                    except:
                        QuickMoves[moveName]["dmgWindow"] = 0
                    # regard hidden power as 18 different moves
                    if moveName == "HIDDEN_POWER_FAST":
                        QuickMoves[moveName]["name"] = "HiddenPowerNormal"
                        for typeName in typeDict:
                            if not typeName == "POKEMON_TYPE_NORMAL":
                                moveType = typeDict[typeName]
                                typeNameShort = typeName[13:].capitalize()
                                moveNameNew = "HIDDEN_POWER_" + typeName[13:] + "_FAST"
                                if not moveNameNew in QuickMoves:
                                    QuickMoves[moveNameNew] = {}
                                QuickMoves[moveNameNew] = QuickMoves[moveName].copy()
                                QuickMoves[moveNameNew]["name"] = "HiddenPower" + typeNameShort
                                QuickMoves[moveNameNew]["type"] = moveType
                                outString += "pve move: " + moveNameNew + "\n"
                else:
                    # this is a charge move
                    if not moveName in ChargeMoves:
                        ChargeMoves[moveName] = {}
                    ChargeMoves[moveName]["num"] = moveNum
                    ChargeMoves[moveName]["name"] = toLowerString(moveName)
                    ChargeMoves[moveName]["type"] = moveType
                    try:
                        ChargeMoves[moveName]["duration"] = int(moveStats["durationMs"]/10)
                    except:
                        ChargeMoves[moveName]["duration"] = 100
                    try:
                        ChargeMoves[moveName]["power"] = int(moveStats["power"])
                    except:
                        ChargeMoves[moveName]["power"] = 0
                    try:
                        ChargeMoves[moveName]["energyDelta"] = -int(moveStats["energyDelta"])
                    except:
                        ChargeMoves[moveName]["energyDelta"] = 50
                    try:
                        ChargeMoves[moveName]["dmgWindow"] = int(moveStats["damageWindowStartMs"]/10)
                    except:
                        ChargeMoves[moveName]["dmgWindow"] = 0
            elif "smeargleMovesSettings" in template["data"]:
                # moves that Smeargle can learn
                for moveName in template["data"]["smeargleMovesSettings"]["quickMoves"]:
                    if not moveName in smeargleQuickMoves:
                        smeargleQuickMoves.append(moveName)
                        # handle hidden power
                        if moveName == "HIDDEN_POWER_FAST":
                            for typeName in typeDict:
                                if not typeName == "POKEMON_TYPE_NORMAL":
                                    typeNameShort = typeName[13:].capitalize()
                                    moveNameNew = "HIDDEN_POWER_" + typeName[13:] + "_FAST"
                                    smeargleQuickMoves.append(moveNameNew)
                for moveName in template["data"]["smeargleMovesSettings"]["cinematicMoves"]:
                    if not moveName in smeargleChargeMoves:
                        smeargleChargeMoves.append(moveName)
                        
        PokemonStats["SMEARGLE"]["quickMoves"] = smeargleQuickMoves
        PokemonStats["SMEARGLE"]["chargeMoves"] = smeargleChargeMoves
        
        # finalize all entries' names
        newDict = {}
        for key in PokemonStats:
            newList = []
            for moveName in PokemonStats[key]["quickMoves"]:
                newList.append(QuickMoves[moveName]["name"])
            PokemonStats[key]["quickMoves"] = newList
            newList = []
            for moveName in PokemonStats[key]["chargeMoves"]:
                newList.append(ChargeMoves[moveName]["name"])
            PokemonStats[key]["chargeMoves"] = newList
            name = PokemonStats[key]["name"]
            newDict[name] = PokemonStats[key]
        PokemonStats = newDict
        newDict = {}
        for key in QuickMoves:
            name = QuickMoves[key]["name"]
            newDict[name] = QuickMoves[key]
        QuickMoves = newDict
        newDict = {}
        for key in ChargeMoves:
            name = ChargeMoves[key]["name"]
            newDict[name] = ChargeMoves[key]
        ChargeMoves = newDict
        
        # copy the manually added entries from the saved dictionaries
        # or initialize new ones
        for pokemonId in PokemonStats:
            if not pokemonId in self.pokemonStats:
                outString += "new pokemon entry: " + pokemonId + "\n"
                PokemonStats[pokemonId]["rLevel"] = "Level1"
                PokemonStats[pokemonId]["url"] = str(PokemonStats[pokemonId]["num"]).rjust(3, "0")
                PokemonStats[pokemonId]["released"] = 0
                PokemonStats[pokemonId]["shinyReleased"] = 0
            else:
                PokemonStats[pokemonId]["rLevel"] = self.pokemonStats[pokemonId]["rLevel"]
                PokemonStats[pokemonId]["url"] = self.pokemonStats[pokemonId]["url"]
                PokemonStats[pokemonId]["released"] = self.pokemonStats[pokemonId]["released"]
                PokemonStats[pokemonId]["shinyReleased"] = self.pokemonStats[pokemonId]["shinyReleased"]
                PokemonStats[pokemonId]["name"] = self.pokemonStats[pokemonId]["name"]
        
        with open(configPath + "PokemonStatsNew.json", "w") as outfile:
            json.dump(PokemonStats, outfile, indent=4)
        with open(configPath + "QuickMovesNew.json", "w") as outfile:
            json.dump(QuickMoves, outfile, indent=4)
        with open(configPath + "ChargeMovesNew.json", "w") as outfile:
            json.dump(ChargeMoves, outfile, indent=4)
        with open(configPath + "GMasterLog.txt", "w", newline="") as outfile:
            outfile.write(outString)

        await ctx.send(okayEmoji + " All entries from GAME_MASTER.json have been processed!")
        
        return
    
    # send the region role signup message
    # key is to save the message id to [emoji, role] mapping
    # only use this when initially setting up or when Niantic changes something major
    @commands.command(pass_context=True)
    async def signupMessageRegion(self, ctx):
        # can only be used by LucaLucaBea
        if not ctx.message.author.id == lucaId:
            return
        
        singupChan = get(self.bot.get_all_channels(), id=signupChanId)
        roleIndex = 0
        roleText = ""
        roleNames = []
        for regionName in regionIds:
            roleNames.append(regionName)
            roleText += accountEmoji[roleIndex] + " " + regionName + "\n"
            roleIndex += 1
        roleText = roleText[:-1]
            
        embed = discord.Embed(title="React here to sign up for region roles", color=defaultColor)
        embed.add_field(name=instructionText, value=roleText, inline=True)
        imgUrl = r"https://i.imgur.com/KT14zwd.png"
        embed.set_thumbnail(url=imgUrl)
        
        message = await singupChan.send(embed=embed)
        
        for iNum in range(len(regionIds)):
            emoji = accountEmoji[iNum]
            await message.add_reaction(emoji)
            
        self.roleDict[str(message.id)] = {}
        self.roleDict[str(message.id)]["type"] = "Region"
        self.roleDict[str(message.id)]["numEmoji"] = len(regionIds)
        self.roleDict[str(message.id)]["roles"] = roleNames
        
        self.writeSignupMsg()

        return
        
    # send all role signup messages in role signup channel
    # key is to save the message id to [emoji, role] mapping
    # only use this when initially setting up or when Niantic changes something major
    @commands.command(pass_context=True)
    async def signupMessage(self, ctx):
        # can only be used by LucaLucaBea
        if not ctx.message.author.id == lucaId:
            return
        # purge sign-up channel
        singupChan = get(self.bot.get_all_channels(), id=signupChanId)
        await singupChan.purge(limit=100)
        self.roleDict = {}
        # recreate all embed messages
        for tierName in tierNamesShort:
            roleNames = []
            for roleIndex, roleId in enumerate(roleIds[tierName]):
                roleName = "Raid" + tierName + "P" + str(roleIndex+1)
                roleNames.append(roleName)
                role = get(ctx.message.guild.roles, id=roleId)
                await role.edit(name=roleName)
                
            embed = discord.Embed(title="React here to sign up for {} raid roles".format(tierName), color=defaultColor)
            embed.add_field(name=instructionText, value="Nothing right now", inline=True)
            imgUrl = raidLevels[tierName]["url"]
            embed.set_thumbnail(url=imgUrl)
                
            message = await singupChan.send(embed=embed)
        
            for iNum in range(len(roleIds[tierName])):
                emoji = accountEmoji[iNum]
                await message.add_reaction(emoji)
            
            self.roleDict[str(message.id)] = {}
            self.roleDict[str(message.id)]["type"] = tierName
            self.roleDict[str(message.id)]["numEmoji"] = len(roleIds[tierName])
            self.roleDict[str(message.id)]["roles"] = roleNames
            
        roleNames = ["RaidLevel5", "RaidElite", "RaidMega", raidShinyName]
        for roleName in roleNames:
            roleId = roleIds[roleName]
            role = get(ctx.message.guild.roles, id=roleId)
            await role.edit(name=roleName)
        
        embed = discord.Embed(title="React here to sign up for General raid roles", color=defaultColor)
        embed.add_field(name=instructionText, value=accountEmoji[0] + " All Level5 bosses\n" 
                                                   +accountEmoji[1] + " All Elite bosses\n"
                                                   +accountEmoji[2] + " All Mega bosses\n"
                                                   +accountEmoji[3] + " All bosses that can be caught as shiny", inline=True)
                
        message = await singupChan.send(embed=embed)
        
        for iNum in range(len(roleNames)):
            emoji = accountEmoji[iNum]
            await message.add_reaction(emoji)
            
        self.roleDict[str(message.id)] = {}
        self.roleDict[str(message.id)]["type"] = "General"
        self.roleDict[str(message.id)]["numEmoji"] = len(roleNames)
        self.roleDict[str(message.id)]["roles"] = roleNames
        
        self.writeSignupMsg()

        return

#---------------------------------------------------------------------------------#
#--------------------------image process functions--------------------------------#
#---------------------------------------------------------------------------------#  

    def matchTemplate(self, imgo, imgt, 
                      tResizeW, tResizeH, maxAttempt,
                      h1, h2, w1, w2, 
                      eCountMin, eCountMax,
                      eh1, eh2, ew1, ew2,                      
                      debugMode, debugName):
        # basic width and height settings
        width0 = 1440.0
        height0 = 2560.0
        width, height = imgo.shape[::-1]
        w, h = imgt.shape[::-1]
        # resize the template while keeping the aspect ratio
        resw = int(tResizeW * width / width0)
        resh = int(tResizeH * height / height0)
        bsize = min(resw, resh)
        imgt = cv.resize(imgt, (bsize, bsize))
        w, h = imgt.shape[::-1]
        # crop the original image based on inputs
        h1 = int(h1 * height)
        h2 = int(h2 * height)
        w1 = int(w1 * width)
        w2 = int(w2 * width)
        imgoCrop = imgo[h1:h2, w1:w2]
        if debugMode:
            cv.imwrite("Crop_" + debugName + ".png", imgoCrop)
        # use varying threshold to find the template
        res = cv.matchTemplate(imgoCrop, imgt, cv.TM_CCOEFF_NORMED)
        threshold = 0.7
        tstep = 0.05
        nAttempt = 0
        maxCnts = 0
        cx0Final = -1.0
        cy0Final = -1.0
        while nAttempt < maxAttempt:
            img2 = imgoCrop.copy() * 0 + 255
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                cv.rectangle(img2, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), -1)
            lvldet = 255 - img2
            
            if debugMode:
                cv.imwrite("Match_" + debugName + str(nAttempt+1) + ".png", lvldet)
                    
            contours, heirarchy = cv.findContours(lvldet.copy(), 
                                                  cv.RETR_EXTERNAL,
                                                  cv.CHAIN_APPROX_SIMPLE) 

            cnts = len(contours)
            
            if cnts > eCountMax:
                print("on_message: found more than " + str(eCountMax) + " " + debugName + ", retrying")
                threshold = threshold + tstep
                nAttempt += 1
            elif cnts < eCountMin:
                print("on_message: found less than " + str(eCountMin) + " " + debugName + ", retrying")
                threshold = threshold - tstep
                nAttempt += 1
            else:
                cxs = 0.0
                cys = 0.0
                cyList = []
                for contour in contours:
                    M = cv.moments(contour)
                    cxs += M["m10"] / M["m00"]
                    cys += M["m01"] / M["m00"]
                    cyList.append(M["m01"] / M["m00"])
                cx = (cxs / float(cnts)) / float(w2-w1)
                cy = (cys / float(cnts)) / float(h2-h1)
                cx0 = (cxs / float(cnts) + float(w1)) / float(width)
                cy0 = (cys / float(cnts) + float(h1)) / float(height)
                if debugMode:
                    print("on_message: the center is at height " + str(cy) + " width " + str(cx))
                # if more than one item, check the heights
                isSameHeight = True
                if eCountMax > 1:
                    for cyItem in cyList:
                        if abs(cyItem - cys / float(cnts)) >= 20.0:
                            isSameHeight = False
                            break
                if cx > ew1 and cx < ew2 and cy > eh1 and cy < eh2 and isSameHeight:
                    print("on_message: found " + str(cnts) + " " + debugName)
                    if eCountMin == eCountMax:
                        return cx0, cy0, cnts
                    else:
                        if cnts > maxCnts:
                            maxCnts = cnts
                            cx0Final = cx0
                            cy0Final = cy0
                threshold = threshold - tstep
                nAttempt += 1
        if eCountMin == eCountMax:
            return -1.0, -1.0, 0
        else:
            return cx0Final, cy0Final, maxCnts   
        
    def findAvailableNames(self, faceCount, isCampfire):
        availableRaids = []
        for tierName in tierNames:
            if tierNames[tierName] == faceCount:
                availableRaids.append(tierName)
        if not isCampfire and faceCount == 5:
            availableRaids.append("Elite")
        # first, find all available names
        nameList1 = []
        for pokemonName in self.pokemonStats:
            if self.pokemonStats[pokemonName]["rLevel"] in availableRaids:
                nameList1.append(pokemonName)
        # second, only find ones that are active right now
        nameList2 = []
        for tierName in availableRaids:
            schedule = self.bossSchedule["last"]
            if (datetime.strptime(schedule["endTime"], timeForm) - 
                timedelta(hours=backHours) > datetime.utcnow() + timedelta(hours=timeZoneHours)):                    
                if tierName in schedule and len(schedule[tierName]) > 0:
                    for pokemonName in schedule[tierName]:
                        nameList2.append(pokemonName)
            for schedule in self.bossSchedule["schedules"]:
                if (schedule["type"] == "Default" and
                    datetime.strptime(schedule["startTime"], timeForm) -
                    timedelta(hours=advanceHours) < datetime.utcnow() + timedelta(hours=timeZoneHours)):
                    if tierName in schedule and len(schedule[tierName]) > 0:
                        for pokemonName in schedule[tierName]:
                            if not pokemonName in nameList2:
                                nameList2.append(pokemonName)
            for schedule in self.bossSchedule["schedules"]:
                if (schedule["type"] == "Event" and
                    datetime.strptime(schedule["startTime"], timeForm) -
                    timedelta(hours=advanceHours) < datetime.utcnow() + timedelta(hours=timeZoneHours) and
                    datetime.strptime(schedule["endTime"], timeForm) -
                    timedelta(hours=backHours) > datetime.utcnow() + timedelta(hours=timeZoneHours)):
                    if tierName in schedule and len(schedule[tierName]) > 0:
                        for pokemonName in schedule[tierName]:
                            if not pokemonName in nameList2:
                                nameList2.append(pokemonName)
            schedule = self.bossSchedule["current"]
            if tierName in schedule and len(schedule[tierName]) > 0:
                for pokemonName in schedule[tierName]:
                    if not pokemonName in nameList2:
                        nameList2.append(pokemonName)
                        
        return nameList1, nameList2
        
    def findAvailableRaids(self, faceCount, isCampfire):
        # first, find all available ones
        nameList1 = []
        for tierName in tierNames:
            if tierNames[tierName] == faceCount:
                nameList1.append(tierName)
        if not isCampfire and faceCount == 5:
            nameList1.append("Elite")
        # second, only find ones that are active right now
        nameList2 = []
        for tierName in nameList1:
            schedule = self.bossSchedule["last"]
            if (datetime.strptime(schedule["endTime"], timeForm) - 
                timedelta(hours=backHours) > datetime.utcnow() + timedelta(hours=timeZoneHours)):                    
                if tierName in schedule and len(schedule[tierName]) > 0:
                    nameList2.append(tierName)
            for schedule in self.bossSchedule["schedules"]:
                if (schedule["type"] == "Default" and
                    datetime.strptime(schedule["startTime"], timeForm) -
                    timedelta(hours=advanceHours) < datetime.utcnow() + timedelta(hours=timeZoneHours)):
                    if tierName in schedule and len(schedule[tierName]) > 0:
                        if not tierName in nameList2:
                            nameList2.append(tierName)
            for schedule in self.bossSchedule["schedules"]:
                if (schedule["type"] == "Event" and
                    datetime.strptime(schedule["startTime"], timeForm) -
                    timedelta(hours=advanceHours) < datetime.utcnow() + timedelta(hours=timeZoneHours) and
                    datetime.strptime(schedule["endTime"], timeForm) -
                    timedelta(hours=backHours) > datetime.utcnow() + timedelta(hours=timeZoneHours)):
                    if tierName in schedule and len(schedule[tierName]) > 0:
                        if not tierName in nameList2:
                            nameList2.append(tierName)
            schedule = self.bossSchedule["current"]
            if tierName in schedule and len(schedule[tierName]) > 0:
                if not tierName in nameList2:
                    nameList2.append(tierName)
                        
        return nameList1, nameList2
        
#---------------------------------------------------------------------------------#
#----------------------------------listeners--------------------------------------#
#---------------------------------------------------------------------------------#  
    
    # process raid screenshots    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id == sightingChanId:
            if len(message.attachments) > 0:
                if not self.chanDict:
                    print("on_message: no cache, rebuilding...")
                    await self.iniChanDict()
                checktime = datetime.utcnow()
                polltime = self.lastRaid + timedelta(seconds=raidCooldownSeconds)
                if checktime < polltime:
                    await message.channel.send(cooldownText)
                    return
                self.lastRaid = datetime.utcnow()
                
                width = int(message.attachments[0].width)
                height = int(message.attachments[0].height)
                print("on_message: image size: " + str(width) + "x" + str(height))
                if width < 600 or height < 900:
                    await message.channel.send(errorEmoji + " The image does not have enough resolution.\n" + 
                          "The resolution needs to be at least 600x900. " + 
                          "Your image was at " + str(width) + "x" + str(height) + ".")
                    return
                    
                submitTime = datetime.utcnow()
                def check1(msg):
                    return msg.channel == message.channel and msg.author == message.author
                    
                async with aiohttp.ClientSession() as session:
                    async with session.get(message.attachments[0].url) as resp:
                        buffer = io.BytesIO(await resp.read())
                buffer.seek(0)
                with open("OriginalImage.png", "wb") as f:
                    shutil.copyfileobj(buffer, f, length=13107200)
                
                imgorig = cv.imread("OriginalImage.png", 0) # grayscale
                cv.imwrite("GrayScaleImage.png", imgorig)
                template = cv.imread("ExitButtonTemplate.png", 0) # grayscale
                imgThres = cv.adaptiveThreshold(imgorig, 255, 
                                                cv.ADAPTIVE_THRESH_MEAN_C,
                                                cv.THRESH_BINARY, 11, 2)
                cv.imwrite("AdaptiveThresImage.png", imgThres)
                cx1, cy1, cnts1 = self.matchTemplate(imgorig, template, 
                                                     172.0, 174.0, 5,
                                                     0.75, 1.0, 0.25, 0.75, 
                                                     1, 1,
                                                     0.0, 1.0, 0.33, 0.67,
                                                     True, "ExitButton")
                
                if cnts1 == 1:
                    isCampfire = False
                    print("on_message: Pokemon GO route")
                else:
                    isCampfire = True
                    print("on_message: Campfire route")
                
                if isCampfire:
                    template = cv.imread("NavButtonTemplate.png", 0) # grayscale
                    cx2, cy2, cnts2 = self.matchTemplate(imgorig, template, 
                                                         112.0, 104.0, 5,
                                                         0.75, 1.0, 0.5, 1.0, 
                                                         1, 1,
                                                         0.0, 1.0, 0.5, 1.0,
                                                         True, "NavButton")
                                                         
                    if not cnts2 == 1:
                        await message.channel.send(errorEmoji + " Failed to determine screenshot type. Please try manual input with %raid or ask <@{}> for help.".format(str(lucaId)))
                        return
                    
                    template = 255 - cv.imread("BossSymTemplate1.png", 0) # grayscale
                    cx3, cy3, cnts3 = self.matchTemplate(imgThres, template, 
                                                         42.0, 40.0, 9,
                                                         1.0-2.0*(1.0-cy2), cy2-0.03, 2.6*(1.0-cx2), cx2, 
                                                         1, 6,
                                                         0.5, 1.0, 0.0, 1.0,
                                                         True, "CampfireBossLevel")                                     
                    print("on_message: found this many faces: " + str(cnts3))
                    
                    imgText = imgThres[int((1.0-2.0*(1.0-cy2))*height):int((cy2-0.03)*height), int(2.6*(1.0-cx2)*width):int(cx2*width)]
                    # Any crop should happen here
                    campfireText = tes.image_to_string(imgText,
                                                       config="--psm 6 --oem 3 -c tessedit_char_whitelist=" + 
                                                       "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 --tessdata-dir " +
                                                       r'"I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                    print("on_message: text read: " + campfireText)
                    
                    testStrs = campfireText.split("\n")
                    foundState = False
                    for index, testStr in enumerate(testStrs):
                        if "starts" in testStr and ("AM" in testStr or "PM" in testStr):
                            foundState = True
                            hatchedboss = False
                            gymnameRead = testStrs[:index]
                            nameRead = ""
                            timeRead = testStr.split("at")[1]
                            timeRead = timeRead[1:]
                            timeRead = "".join(char for char in timeRead if (char.isalnum() or char == " " or char == ":"))
                            timeRead = timeRead.strip()
                            print("on_message: unhatched boss on Campfire")
                        elif "Ends" in testStr and ("AM" in testStr or "PM" in testStr):
                            foundState = True
                            hatchedboss = True
                            gymnameRead = testStrs[:index]
                            nameRead = testStr.split("Ends")[0].strip()
                            nameRead = "".join(char for char in nameRead if char.isalnum())
                            timeRead = testStr.split("Ends")[1]
                            timeRead = timeRead[1:]
                            timeRead = "".join(char for char in timeRead if (char.isalnum() or char == " " or char == ":"))
                            timeRead = timeRead.strip()
                            print("on_message: hatched boss on Campfire")
                    if not foundState:
                        await message.channel.send(errorEmoji + " Failed to determine raid status. Please try manual input with %raid or ask <@{}> for help.".format(str(lucaId)))
                        return
                    # process the gym name    
                    gymname = ""
                    newGymNameRead = []
                    for line in gymnameRead:
                        if line.strip():
                            newGymNameRead.append(line)
                    numLines = len(newGymNameRead)
                    for index, line in enumerate(newGymNameRead):
                        line = "".join(char for char in line if (char.isalnum() or char == " "))
                        line = line.strip()
                        if index == 0 and numLines > 1 and len(line) < 12:
                            continue
                        if len(line) > 32:
                            continue
                        if index == 0 and numLines > 1:
                            lineWords = line.split(" ")
                            totalWords = len(lineWords)
                            wordCount = 0
                            print("on_message: total words in line: " + str(totalWords))
                            for lineWord in lineWords:
                                if wordDict.check(lineWord):
                                    wordCount += 1
                                    print("on_message: this is a word: " + lineWord)
                            if not wordCount == totalWords:
                                continue
                        if line:
                            gymname += line + " "
                    gymname = gymname.strip()
                    
                    if hatchedboss:
                        endTime = datetime.combine(dt.date.today(), datetime.strptime(timeRead, timeFormShorter).time())
                        print("on_message: end time: " + str(endTime))
                        raidTimer = endTime - datetime.utcnow() - timedelta(hours=timeZoneHours)
                        raidTimer = raidTimer.total_seconds()
                        raidTimer = int(divmod(raidTimer, 60)[0])
                        print("on_message: time difference: " + str(raidTimer))
                        if raidTimer < urgentMinutes and raidTimer >= 0:
                            await message.channel.send(errorEmoji + r" Sorry, there is too little time (<{} minutes) left on this raid. The raid will not be created.".format(str(urgentMinutes)))
                            return
                        if raidTimer < 0:
                            raidTimer = raidTimer + 1440
                        
                        availableNames1, availableNames2 = self.findAvailableNames(cnts3, True)
                        
                        nameRead = "".join(char for char in nameRead if char.isalnum())
                        maxratio = 0.0
                        stonam = ""
                        for y in availableNames1:
                            displayName = self.pokemonStats[y]["name"]
                            gr = SequenceMatcher(None, nameRead.upper(), displayName.upper()).ratio()
                            if gr > maxratio:
                                maxratio = gr
                                stonam = y
                        print("on_message: Raw: " + stonam + "-->" + str(maxratio))
                        
                        nameList = [stonam]
                        displayName0 = self.pokemonStats[stonam]["name"]
                        for y in availableNames1:
                            displayName = self.pokemonStats[y]["name"]
                            if displayName == displayName0 and not y in nameList:
                                nameList.append(y)
                        
                        if len(nameList) == 1:
                            stonam = nameList[0]
                        else:
                            outputString = message.author.mention + " Please choose a name from the following list. Type a number:\n"
                            for index, name in enumerate(nameList):
                                outputString += "{}.{} ".format(str(index+1), name)
                            await message.channel.send(outputString)
                            try:
                                msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                            except:
                                await message.channel.send(errorEmoji + " Timeout.")
                                return
                            try:
                                nameNum = int(msg.content) 
                            except:
                                await message.channel.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                                return
                            if nameNum > len(nameList) or nameNum < 1:
                                await message.channel.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                                return
                            stonam = nameList[nameNum-1]
                    else:
                        startTime = datetime.combine(dt.date.today(), datetime.strptime(timeRead, timeFormShorter).time())
                        print("on_message: start time:" + str(startTime))
                        raidTimer = startTime - datetime.utcnow() - timedelta(hours=timeZoneHours)
                        raidTimer = raidTimer.total_seconds()
                        raidTimer = int(divmod(raidTimer, 60)[0])
                        print("on_message: time difference:" + str(raidTimer))
                        if raidTimer < 0:
                            raidTimer = raidTimer + 1440
                            
                        availableRaids1, availableRaids2 = self.findAvailableRaids(cnts3, True)
                        
                        stonam = ""
                        if len(availableRaids2) == 0:
                            availableRaids2 = availableRaids1
                        if len(availableRaids2) == 1:
                            stonam = availableRaids2[0]
                        else:
                            outputString = message.author.mention + " Please choose a raid level from the following list. Type a number:\n"
                            for index, name in enumerate(availableRaids2):
                                outputString += "{}.{} ".format(str(index+1), name)
                            await message.channel.send(outputString)
                            try:
                                msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                            except:
                                await message.channel.send(errorEmoji + " Timeout.")
                                return
                            try:
                                nameNum = int(msg.content) 
                            except:
                                await message.channel.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                                return
                            if nameNum > len(availableRaids2) or nameNum < 1:
                                await message.channel.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                                return
                            stonam = availableRaids2[nameNum-1]
                else:
                    template = cv.imread("BossSymTemplate2.png", 0) # grayscale
                    cx3, cy3, cnts3 = self.matchTemplate(imgThres, template, 
                                                         84.0, 72.0, 9,
                                                         0.05, 0.4, 0.2, 0.8, 
                                                         1, 6,
                                                         0.0, 0.5, 0.33, 0.67,
                                                         True, "PokemonGOBossLevel")
                    print("on_message: found this many faces with method 1: " + str(cnts3))

                    if cnts3 > 0:
                        hatchedboss = True
                    else:
                        hatchedboss = False
                        cx3, cy3, cnts3 = self.matchTemplate(imgThres, template, 
                                                             112.0, 104.0, 9,
                                                             0.2, 0.4, 0.2, 0.8, 
                                                             1, 6,
                                                             0.0, 1.0, 0.0, 1.0,
                                                             True, "PokemonGOBossEggLevel")
                        print("on_message: found this many faces with method 2: " + str(cnts3))
                    
                    if cnts3 == 0:
                        await message.channel.send(errorEmoji + " Failed to read raid level. Please try manual input with %raid or ask <@{}> for help.".format(str(lucaId)))
                        return

                    if hatchedboss:
                        imgText = imgorig[int(0.23*height):int(0.37*height), int(0.07*width):int(0.93*width)]
                        w2, h2 = imgText.shape[::-1]
                        cv.imwrite("Crop_BossName.png", imgText)
                        
                        final_strs = []
                        for nThres in range(252, 255):
                            gray, thresh = cv.threshold(imgText, nThres, 255, cv.THRESH_BINARY)
                            
                            contours, heirarchy = cv.findContours(thresh, 
                                                                  cv.RETR_EXTERNAL, 
                                                                  cv.CHAIN_APPROX_SIMPLE)
                            cv.imwrite("Thres_BossNameDirect" + str(nThres) + ".png", thresh)
                            test_str_1 = tes.image_to_boxes(thresh,
                                                            config="--psm 7 --oem 3 -c tessedit_char_whitelist=" + 
                                                            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 --tessdata-dir " +
                                                            r'"I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                        
                            test_str_1 = test_str_1.split("\n")
                            strrr = "".join(b.split(" ")[0] for b in test_str_1)
                            strrr = "".join(char for char in strrr if char.isalnum())
                            final_strs.append(strrr)
                            print("on_message: final_str_1_" + str(nThres) + ": " + strrr)
                        
                            for cnt, contour in enumerate(contours):
                                x, y, w, h = cv.boundingRect(contour)
                                if x <= 2 or y <= 5 or x + w >= w2 - 5 or y + h >= h2 - 5:
                                    cv.drawContours(image=thresh,
                                                    contours=contours,
                                                    contourIdx=cnt,
                                                    color=(0, 0, 0),
                                                    thickness=cv.FILLED)
                    
                            contours, heirarchy = cv.findContours(thresh, 
                                                                  cv.RETR_EXTERNAL,
                                                                  cv.CHAIN_APPROX_SIMPLE)
                        
                            chu1 = int(0.05 * height)
                            chu2 = int(0.04 * height)
                            thresho = int(0.01 * height)
                            for cnt, contour in enumerate(contours):
                                x, y, w, h = cv.boundingRect(contour)
                                if cv.contourArea(contour) < 100 or (abs(h - chu1) > thresho and abs(h - chu2) > thresho):
                                    cv.drawContours(image=thresh,
                                                    contours=contours,
                                                    contourIdx=cnt,
                                                    color=(0, 0, 0),
                                                    thickness=cv.FILLED)
                                
                            cv.imwrite("Thres_BossNameFill" + str(nThres) + ".png", thresh)
                            test_str_2 = tes.image_to_string(thresh,
                                                             config="--psm 7 --oem 3 -c tessedit_char_whitelist=" +
                                                             "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 --tessdata-dir " +
                                                             r'"I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                            test_str_2 = test_str_2.split("\n")
                            test_str_2 = test_str_2[0]
                            strrr = "".join(char for char in test_str_2 if char.isalnum())
                            final_strs.append(strrr)
                            print("on_message: final_str_2_" + str(nThres) + ": " + strrr)

                        # find out the time remaining    
                        addloff = 10
                        gottime = False
                        imgTime = cv.threshold(imgorig, 230, 255, cv.THRESH_BINARY)[1]
                    
                        for rn in range(0, 20):
                            imgTimeCrop = 255 - imgTime[int(0.54*height)+addloff*rn:int(0.60*height)+addloff*rn, int(0.73*width):int(0.95*width)]
                            cv.imwrite("Crop_TimeHatched" + str(rn+1) + ".png", imgTimeCrop)
                            timerem1 = tes.image_to_string(imgTimeCrop,
                                                           config="--psm 7 --oem 3 -c tessedit_char_whitelist=" +
                                                                  r'0123456789: --tessdata-dir "I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                            timerem2 = tes.image_to_string(imgTimeCrop,
                                                           config="--psm 12 --oem 3 -c tessedit_char_whitelist=" +
                                                                  r'0123456789: --tessdata-dir "I:\Program Files (x86)\Tesseract-OCR\tessdata"')

                            timerem = "".join(e for e in timerem1 if (e.isdigit() or e == ":"))
                            print("on_message: timer read 1_" + str(rn+1) + ": " + timerem)
                            if ":" in timerem:
                                newcont = timerem.split(":")
                                if len(newcont) == 3:
                                    if int(newcont[1]) >= 0 and int(newcont[1]) < 60:
                                        if int(newcont[2]) >= 0 and int(newcont[2]) < 60:
                                            if int(newcont[0]) >= 0 and int(newcont[0]) < 24:
                                                gottime = True
                                                break
                            
                            timerem = "".join(e for e in timerem2 if (e.isdigit() or e == ":"))
                            print("on_message: timer read 2_" + str(rn+1) + ": " + timerem)
                            if ":" in timerem:
                                newcont = timerem.split(":")
                                if len(newcont) == 3:
                                    if int(newcont[1]) >= 0 and int(newcont[1]) < 60:
                                        if int(newcont[2]) >= 0 and int(newcont[2]) < 60:
                                            if int(newcont[0]) >= 0 and int(newcont[0]) < 24:
                                                gottime = True
                                                break

                        if not gottime:
                            await message.channel.send(errorEmoji + " Failed to read raid timer.")
                            return
                        timerem = timerem.strip()
                        print("on_message: the amount of time remaining is: " + timerem)
                        newtimerem = re.sub(r"\s+", "", timerem)
                        arrgs = newtimerem.split(":")
                        raidTimer = int(arrgs[1]) + 60 * int(arrgs[0])
                        if int(arrgs[1]) < urgentMinutes:
                            await message.channel.send(errorEmoji + r" Sorry, there is too little time (<{} minutes) left on this raid. The raid will not be created.".format(str(urgentMinutes)))
                            return

                        maxratio = 0.0
                        stonam = ""
                        availableNames1, availableNames2 = self.findAvailableNames(cnts3, False)
                        for y in availableNames1:
                            displayName = self.pokemonStats[y]["name"]
                            for final_str in final_strs:
                                gr = SequenceMatcher(None, final_str.upper(), displayName.upper()).ratio()
                                if gr > maxratio:
                                    maxratio = gr
                                    stonam = y        
                        print("on_message: Raw: " + stonam + "-->" + str(maxratio))
                            
                        if maxratio < confidenceRaw:
                            maxratio2 = 0.0
                            nameList = []
                            stonam = ""
                            for y in availableNames2:
                                displayName = self.pokemonStats[y]["name"]
                                for final_str in final_strs:
                                    gr = SequenceMatcher(None, final_str.upper(), displayName.upper()).ratio()
                                    if gr > maxratio2:
                                        maxratio2 = gr
                                        stonam = y
                                        if gr >= confidenceLower and not y in nameList:
                                            nameList.append(y)                                            
                            print("on_message: Relative: " + stonam + "-->" + str(maxratio2))
                            
                            if maxratio2 < confidenceRelative and not (maxratio2 > confidenceRelativeLower and len(nameList) == 1):
                                if maxratio2 < confidenceLower:
                                    if len(availableNames2) > 1:
                                        await message.channel.send(message.author.mention + " I'm not confident I can read the raid boss' name. Please type the name for me:")
                                        try:
                                            msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                                        except:
                                            await message.channel.send(errorEmoji + " Timeout.")
                                            return
                                        msgText = msg.content.replace(" ", "")
                                        stonam = await self.handleNames(message.channel, msgText, self.pokemonStats, True, message.author)
                                        if not stonam:
                                            await message.channel.send(errorEmoji + ' Failed to process Pokemon name "{}", please try manual input with %raid or ask <@{}> for help.'.format(str(lucaId)))
                                            return
                                    else:
                                        stonam = availableNames2[0]
                                else:
                                    if len(nameList) == 1:
                                        stonam = nameList[0]
                                    else:
                                        outputString = message.author.mention + " Please choose a name from the following list. Type a number:\n"
                                        for index, name in enumerate(nameList):
                                            outputString += "{}.{} ".format(str(index+1), name)
                                        await message.channel.send(outputString)
                                        try:
                                            msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                                        except:
                                            await message.channel.send(errorEmoji + " Timeout.")
                                            return
                                        try:
                                            nameNum = int(msg.content) 
                                        except:
                                            await message.channel.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                                            return
                                        if nameNum > len(nameList) or nameNum < 1:
                                            await message.channel.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                                            return
                                        stonam = nameList[nameNum-1]
                        else:
                            nameList = [stonam]
                            displayName0 = self.pokemonStats[stonam]["name"]
                            for y in availableNames1:
                                displayName = self.pokemonStats[y]["name"]
                                if displayName == displayName0 and not y in nameList:
                                    nameList.append(y)
                            if not nameList:
                                await message.channel.send(errorEmoji + " Failed to process Pokemon name. Please try manual input with %raid or ask <@{}> for help.".format(str(lucaId)))
                                return
                            elif len(nameList) == 1:
                                stonam = nameList[0]
                            else:
                                outputString = message.author.mention + " Please choose a name from the following list. Type a number:\n"
                                for index, name in enumerate(nameList):
                                    outputString += "{}.{} ".format(str(index+1), name)
                                await message.channel.send(outputString)
                                try:
                                    msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                                except:
                                    await message.channel.send(errorEmoji + " Timeout.")
                                    return
                                try:
                                    nameNum = int(msg.content) 
                                except:
                                    await message.channel.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                                    return
                                if nameNum > len(nameList) or nameNum < 1:
                                    await message.channel.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                                    return
                                stonam = nameList[nameNum-1]

                        print("on_message: Final Pokemon name: " + stonam)
                    
                        # read the gym name
                        imgGym = imgorig[int(0.06*height):int(0.16*height), int(0.23*width):int(0.83*width)]
                        imgGym = cv.threshold(imgGym, 245, 255, cv.THRESH_BINARY)[1]
                        imgGym = 255 - imgGym
                        cv.imwrite("Crop_GymName.png", imgGym)
                        contents2 = tes.image_to_string(imgGym,
                                                        config="--psm 6 --oem 3 -c tessedit_char_whitelist=" +
                                                               "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 --tessdata-dir " +
                                                               r'"I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                        print("on_message: gym name read: " + contents2)
                        gymname = " ".join(word.capitalize() for word in contents2.split())

                    else:
                        imgTime = cv.threshold(imgorig, 230, 255, cv.THRESH_BINARY)[1]
                    
                        addloff = 10
                        gottime = False
                    
                        for rn in range(0, 20):
                            if (height / width) > 2.0:
                                imgTimeCrop = 255 - imgTime[int(0.21*height)+addloff*rn:int(0.3*height)+addloff*rn, int(0.36*width):int(0.64*width)]
                            else:
                                imgTimeCrop = 255 - imgTime[int(0.16*height)+addloff*rn:int(0.24*height)+addloff*rn, int(0.36*width):int(0.64*width)]
                            
                            timerem1 = tes.image_to_string(imgTimeCrop,
                                                           config="--psm 7 --oem 3 -c tessedit_char_whitelist=" +
                                                                  r'0123456789: --tessdata-dir "I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                            timerem2 = tes.image_to_string(imgTimeCrop,
                                                           config="--psm 12 --oem 3 -c tessedit_char_whitelist=" +
                                                                  r'0123456789: --tessdata-dir "I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                            cv.imwrite("Crop_TimeEgg" + str(rn+1) + ".png", imgTimeCrop)
                        
                            timerem = "".join(e for e in timerem1 if (e.isdigit() or e == ":"))
                            print("on_message: timer read 1_" + str(rn+1) + ": " + timerem)
                            if ":" in timerem:
                                newcont = timerem.split(":")
                                if len(newcont) == 3:
                                    if int(newcont[1]) >= 0 and int(newcont[1]) < 60:
                                        if int(newcont[2]) >= 0 and int(newcont[2]) < 60:
                                            if int(newcont[0]) >= 0 and int(newcont[0]) < 24:
                                                gottime = True
                                                break
                            
                            timerem = "".join(e for e in timerem2 if (e.isdigit() or e == ":"))
                            print("on_message: timer read 2_" + str(rn+1) + ": " + timerem)
                            if ":" in timerem:
                                newcont = timerem.split(":")
                                if len(newcont) == 3:
                                    if int(newcont[1]) >= 0 and int(newcont[1]) < 60:
                                        if int(newcont[2]) >= 0 and int(newcont[2]) < 60:
                                            if int(newcont[0]) >= 0 and int(newcont[0]) < 24:
                                                gottime = True
                                                break
                        if not gottime:
                            await message.channel.send(errorEmoji + " Failed to read raid timer.")
                            return
                        timerem = timerem.strip()
                        print("on_message: the amount of time remaining is: " + timerem)
                        newtimerem = re.sub(r"\s+", "", timerem)
                        arrgs = newtimerem.split(":")
                        raidTimer = int(arrgs[1]) + 60 * int(arrgs[0])

                        # read the gym name
                        imgGym = imgorig[int(0.06*height):int(0.16*height), int(0.23*width):int(0.83*width)]
                        imgGym = cv.threshold(imgGym, 245, 255, cv.THRESH_BINARY)[1]
                        imgGym = 255 - imgGym
                        cv.imwrite("Crop_GymName.png", imgGym)
                        contents2 = tes.image_to_string(imgGym,
                                                        config="--psm 6 --oem 3 -c tessedit_char_whitelist=" +
                                                               "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 --tessdata-dir " +
                                                               r'"I:\Program Files (x86)\Tesseract-OCR\tessdata"')
                        print("on_message: gym name read: " + contents2)
                        gymname = " ".join(word.capitalize() for word in contents2.split())
                    
                        availableRaids1, availableRaids2 = self.findAvailableRaids(cnts3, False)
                        
                        stonam = ""
                        if len(availableRaids2) == 0:
                            availableRaids2 = availableRaids1
                        if len(availableRaids2) == 1:
                            stonam = availableRaids2[0]
                        else:
                            outputString = message.author.mention + " Please choose a raid level from the following list. Type a number:\n"
                            for index, name in enumerate(availableRaids2):
                                outputString += "{}.{} ".format(str(index+1), name)
                            await message.channel.send(outputString)
                            try:
                                msg = await self.bot.wait_for("message", timeout=timeoutSeconds, check=check1)
                            except:
                                await message.channel.send(errorEmoji + " Timeout.")
                                return
                            try:
                                nameNum = int(msg.content) 
                            except:
                                await message.channel.send(errorEmoji + ' Answer "{}" is not a number.'.format(msg.content))
                                return
                            if nameNum > len(availableRaids2) or nameNum < 1:
                                await message.channel.send(errorEmoji + ' Answer "{}" is out of range.'.format(msg.content))
                                return
                            stonam = availableRaids2[nameNum-1]  
                    
                if hatchedboss:    
                    await message.channel.send(okayEmoji + " Read a hatched " + stonam + " raid boss at " + 
                                               gymname + " with " + str(raidTimer) + " minutes left. Your raid input has been added to the queue.")
                    
                    isDupe = await self.findDuplicateChan(message.channel, gymname, message.author, True)
                    if not isDupe:
                        gymnameNew = await self.handlePlaceNames(message.channel, gymname, self.gymDict, True, message.author)
                        if not gymnameNew:
                            gymnameNew = gymname
                        else:
                            gymnameNew = self.gymDict[gymnameNew]["name"]
                    
                        channelId = await self.createRaid(2, stonam, raidTimer, gymnameNew, submitTime)
            
                        if channelId:
                            await message.channel.send(okayEmoji + " Raid created, please head to <#{}> for raid coordination!".format(str(channelId)))
                            await self.monitorRaid(channelId)
                            return
                        else:
                            await message.channel.send(errorEmoji + " Failed to find available raid channel. Please ask <@{}> for help.\n".format(str(lucaId)))
                            return
                    else:
                        await message.channel.send(notifEmoji + " Raid creation cancelled.\n")
                        return
                    
                    return
                
                else:   
                    await message.channel.send(okayEmoji + " Read a " + stonam + " raid boss (egg) at " + 
                                               gymname + " with " + str(raidTimer) + " minutes before starting. Your raid input has been added to the queue.")
                        
                    isDupe = await self.findDuplicateChan(message.channel, gymname, message.author, True)
                    if not isDupe:
                        gymnameNew = await self.handlePlaceNames(message.channel, gymname, self.gymDict, True, message.author)
                        if not gymnameNew:
                            gymnameNew = gymname
                        else:
                            gymnameNew = self.gymDict[gymnameNew]["name"]
                    
                        channelId = await self.createRaid(1, stonam, raidTimer, gymnameNew, submitTime)
            
                        if channelId:
                            await message.channel.send(okayEmoji + " Raid created, please head to <#{}> for raid coordination!".format(str(channelId)))
                            await self.monitorRaid(channelId)
                            return
                        else:
                            await message.channel.send(errorEmoji + " Failed to find available raid channel. Please ask <@{}> for help.\n".format(str(lucaId)))
                            return
                    else:
                        await message.channel.send(notifEmoji + " Raid creation cancelled.\n")
                        return
                    
                    return
        
        else:
            return        
        
        return      
        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self.chanDict:
            print("on_raw_reaction_add: no cache, rebuilding...")
            await self.iniChanDict()
        
        message_id = str(payload.message_id)
        if message_id in self.roleDict:
            print("on_raw_reaction_add: reaction added under role signup message")
            if str(payload.emoji) in accountEmoji and accountEmoji.index(str(payload.emoji)) < self.roleDict[message_id]["numEmoji"]:
                print("on_raw_reaction_add: permissible emoji")
                guild_id = payload.guild_id
                user_id = payload.user_id
                guild = await self.bot.fetch_guild(guild_id)
                member = payload.member
                roleIndex = accountEmoji.index(str(payload.emoji))
                roleName = self.roleDict[message_id]["roles"][roleIndex]
                role = get(guild.roles, name=roleName)
                if not role in member.roles and not member.bot:
                    await member.add_roles(role)
                    print("on_raw_reaction_add: added {} role to {}".format(roleName, member.name))
            else:
                print("on_raw_reaction_add: not a permissible emoji")
                return
        else:
            return
            
        return
        
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not self.chanDict:
            print("on_raw_reaction_remove: no cache, rebuilding...")
            await self.iniChanDict()
            
        message_id = str(payload.message_id)
        if message_id in self.roleDict:
            print("on_raw_reaction_remove: reaction removed under role signup message")
            if str(payload.emoji) in accountEmoji and accountEmoji.index(str(payload.emoji)) < self.roleDict[message_id]["numEmoji"]:
                print("on_raw_reaction_remove: permissible emoji")
                guild_id = payload.guild_id
                user_id = payload.user_id
                guild = await self.bot.fetch_guild(guild_id)
                member = await guild.fetch_member(user_id)
                roleIndex = accountEmoji.index(str(payload.emoji))
                roleName = self.roleDict[message_id]["roles"][roleIndex]
                role = get(guild.roles, name=roleName)
                if role in member.roles and not member.bot:
                    await member.remove_roles(role)
                    print("on_raw_reaction_remove: removed {} role from {}".format(roleName, member.name))
            else:
                print("on_raw_reaction_remove: not a permissible emoji")
                return
        else:
            return
            
        return               
        
    # two set of reactions to monitor:
    # 1. within raid role sign up channel, need to assign roles
    # 2. within each active raid channels, need to edit embed fields
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        if not reaction.message.channel.id in raidChanIds and not reaction.message.channel.id == signupChanId:
            return
        chanId = reaction.message.channel.id
        if chanId in raidChanIds:
            if reaction.message.id in self.chanDict[chanId]["embedTimes"]:
                print("on_reaction_add: got a reaction under a group signup embed")
                if isinstance(reaction.emoji, str):
                    if reaction.emoji in accountEmoji:
                        numAdd = accountEmoji.index(reaction.emoji) + 1
                        print("on_reaction_add: default emoji: " + str(numAdd))
                        print(reaction.emoji.encode("utf-8"))
                        if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                        self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["num"] = numAdd
                        await self.signupUpdate(reaction.message, chanId)
                    #if reaction.emoji.name == inpersonEmojiName:
                    elif reaction.emoji == inpersonEmojiString:
                        #print("on_reaction_add: custom emoji: " + reaction.emoji.name)
                        if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                        self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["in-person"] = 1
                        await self.signupUpdate(reaction.message, chanId)
                    #elif reaction.emoji.name == remoteEmojiName:
                    elif reaction.emoji == remoteEmojiString:
                        #print("on_reaction_add: custom emoji: " + reaction.emoji.name)
                        numSignups = 0
                        if len(self.chanDict[chanId]["signupLists"][reaction.message.id]) > 0:
                            for userId in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                                if "remote" in self.chanDict[chanId]["signupLists"][reaction.message.id][userId] and self.chanDict[chanId]["signupLists"][reaction.message.id][userId]["remote"]:
                                    numSignups += 1
                        if numSignups < 5:
                            if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                                self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["remote"] = 1
                            await self.signupUpdate(reaction.message, chanId)
                        else:
                            await reaction.remove(user)
                            return
                    #elif reaction.emoji.name == hostEmojiName:
                    elif reaction.emoji == hostEmojiString:
                        #print("on_reaction_add: custom emoji: " + reaction.emoji.name)
                        alreadyHasHost = False
                        if len(self.chanDict[chanId]["signupLists"][reaction.message.id]) > 0:
                            for userId in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                                if "host" in self.chanDict[chanId]["signupLists"][reaction.message.id][userId] and self.chanDict[chanId]["signupLists"][reaction.message.id][userId]["host"]:
                                    alreadyHasHost = True
                                    break
                        if not alreadyHasHost:
                            if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                                self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["host"] = 1
                            await self.signupUpdate(reaction.message, chanId)
                        else:
                            await reaction.remove(user)
                            return
                    else:
                        print("on_reaction_add: not a permissible emoji, exiting")
                        return     
            else:
                return
            
        return
        
    # two set of reactions to monitor:
    # 1. within raid role sign up channel, need to assign roles
    # 2. within each active raid channels, need to edit embed fields
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return
        if not reaction.message.channel.id in raidChanIds and not reaction.message.channel.id == signupChanId:
            return
        chanId = reaction.message.channel.id
        if chanId in raidChanIds:
            if reaction.message.id in self.chanDict[chanId]["embedTimes"]:
                print("on_reaction_remove: a reaction was removed under a group signup embed")
                if isinstance(reaction.emoji, str):
                    if reaction.emoji in accountEmoji:
                        numAdd = accountEmoji.index(reaction.emoji) + 1
                        print("on_reaction_remove: default emoji: " + str(numAdd))
                        if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                        self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["num"] = 0
                        await self.signupUpdate(reaction.message, chanId)
                    #if reaction.emoji.name == inpersonEmojiName:
                    elif reaction.emoji == inpersonEmojiString:
                        #print("on_reaction_remove: custom emoji: " + reaction.emoji.name)
                        if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                        self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["in-person"] = 0
                        await self.signupUpdate(reaction.message, chanId)
                    #elif reaction.emoji.name == remoteEmojiName:
                    elif reaction.emoji == remoteEmojiString:
                        #print("on_reaction_remove: custom emoji: " + reaction.emoji.name)
                        if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                        self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["remote"] = 0
                        await self.signupUpdate(reaction.message, chanId)
                    #elif reaction.emoji.name == hostEmojiName:
                    elif reaction.emoji == hostEmojiString:
                        #print("on_reaction_remove: custom emoji: " + reaction.emoji.name)
                        if not user.id in self.chanDict[chanId]["signupLists"][reaction.message.id]:
                            self.chanDict[chanId]["signupLists"][reaction.message.id][user.id] = {}
                        self.chanDict[chanId]["signupLists"][reaction.message.id][user.id]["host"] = 0
                        await self.signupUpdate(reaction.message, chanId)
                    else:
                        print("on_reaction_remove: not a permissible custom emoji, exiting")
                        return     
            else:
                return
            
        return
                        
def setup(bot):
    bot.add_cog(Smeargle(bot))