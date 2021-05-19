
import os
import traceback

import discord
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup

from squeak import catalog, whereis

MOUSE_PREFIX = os.environ.get("MOUSE_PREFIX", ".")

MOUSE_HELP = discord.Embed()
MOUSE_HELP.title = "Commands"
MOUSE_HELP.description = (
   "`{pre}mit` for help\n"
   "`{pre}mit [class]` to search the catalog\n"
   "`{pre}map [place]` to search the map"
).format(pre=MOUSE_PREFIX)
MOUSE_HELP.add_field(
   name="Code",
   value="[almonds0166/finneasj](https://github.com/almonds0166/finneasj)"
)
MOUSE_HELP.add_field(
   name="Other",
   value=(
      "[🔬 How I work](https://youtu.be/25LYVxTUZhM)\n"
      "[🐭 More about me](https://thirdwest.scripts.mit.edu/~thirdwest/wiki/index.php?title=User:Finneasj)\n"
      "`almonds` for help/feedback\n"
      "[Slash commands](https://blog.discord.com/slash-commands-are-here-8db0a385d9e6) coming Soon..!"
   )
)

class FinneasJ(discord.Client):
   async def on_message(self, msg):
      if msg.author.bot or not msg.content.startswith(MOUSE_PREFIX): return
      
      cmd, *args = msg.clean_content[len(MOUSE_PREFIX) :].split(" ")
      if cmd in ("mit", "map", "whereis"):
         async with msg.channel.typing():
            if not args:
               await msg.channel.send("Squeak!", embed=MOUSE_HELP)
               return

            query = " ".join(args) # search query

            if cmd == "mit": # search catalog
               c = await catalog.search(query, style="verbatim")
               if c.num_results:
                  await msg.channel.send(c.content, embed=c.embed)
               else:
                  await msg.channel.send("I couldn't find any results for that query!")
               return

            elif cmd in ("map", "whereis"): # search map
               m = await whereis.search(query)
               if m.num_results:
                  await msg.channel.send(m.content, embed=m.embed)
               else:
                  await msg.channel.send("I couldn't find any results for that query!")
               return

   async def on_error(self, event, *args, **kwargs):
      error = traceback.format_exc()
      embed = discord.Embed()
      embed.description = "event: {}\nargs: {}\nkwargs: {}".format(event, args, kwargs)
      if "ERROR_CHANNEL" not in os.environ:
         print("Error! :(")
         print("vvvvvvvvv")
         print(f"```\n{error}\n```")
         print(embed.description)
         print("^^^^^^^^^")
      else:
         error_channel = client.get_channel(int(os.environ["ERROR_CHANNEL"]))
         await error_channel.send("```\n" + error + "\n```", embed=embed)

   async def on_ready(self):
      print("Logged in.")

if __name__ == "__main__":
   client = FinneasJ()
   print("Logging in...")
   client.run(os.environ["MOUSE_TOKEN"])

   print("Logged out.")
