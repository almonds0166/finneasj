
import os
from random import randint

import discord
import asyncio

from mit_catalog import mit_search

#

ESP_PREFIX = "."
ESP_GAME   = ""

MSG_ENTRANCE = """
Hi, I'm Finneas Jawsen!
I haven't declared my major yet oops
My favorite food is whatever's in the TVL or kitchen
"""

MSG_HELP = """
Commands: `{pre}mit`, `{pre}help`, `{pre}game`
More about me: {url}
"""

HELP_LINK = "https://thirdwest.scripts.mit.edu/~thirdwest/wiki/index.php?title=User:Finneasj"

MSG_GAME = "I'm playing {} now"

#

client = discord.Client()

def add_squeaks(words):
   out = words.split(" ") if type(words) == str else words.copy()
   squeaks = 0
   while squeaks < min(10, max(0, randint(-1, 1 + len(out) // 3))):
      squeaks += 1
      out.insert(randint(0, len(out)), "\\*squeak\\*")
   return " ".join(out).replace("squeak\\* \\*squeak", "squeak squeak")

async def cmd_mit(query):
   content, title, url, description = await mit_search(query)
   embed = None
   if title or description:
      embed = discord.Embed()
      embed.title = title
      embed.description = description
      embed.url = url
      if not title: embed.set_image(url=url)
   return content, embed

async def get_previous_message(msg):
   # returns the message clean_content, not the message object itself
   logs = client.logs_from(msg.channel, limit=10, reverse=True)
   messages = []
   async for message in logs:
      messages.append(message)
   for m in sorted(messages, reverse=True, key=lambda m: m.timestamp):
      if m.timestamp < msg.timestamp: return m.clean_content
   return ""

@client.event
async def on_message(msg):
   if msg.author.bot or not msg.content.startswith(ESP_PREFIX): return
   
   cmd, *args = msg.clean_content[len(ESP_PREFIX) :].split(" ")

   if cmd == "mit":
      arg = " ".join(args) if args else await get_previous_message(msg)
      content, embed = await cmd_mit(arg)
      await client.send_message(msg.channel, content, embed=embed)

   elif cmd == "help":
      await client.send_message(msg.channel,
         add_squeaks(MSG_HELP).format(pre=ESP_PREFIX, url=HELP_LINK))

   elif cmd == "game":
      arg = " ".join(args)
      await client.change_presence(game=discord.Game(name=arg))
      if arg:
         await client.send_message(msg.channel, add_squeaks(MSG_GAME.format(arg)))

@client.event
async def on_server_join(server):
   starting_channel = server.default_channel if server.default_channel else sorted(server.channels, key=lambda c: c.position)[0]
   await client.send_message(starting_channel, add_squeaks(MSG_ENTRANCE))

@client.event
async def on_ready():
   if ESP_GAME: await client.change_presence(game=discord.Game(name=ESP_GAME))
   print("Logged in.")

#

print("Logging in...")
client.run(os.environ["MOUSE_ENVIRON"], bot=True)

print("Logged out.")