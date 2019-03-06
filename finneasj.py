
import os
import traceback

import discord
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup

MOUSE_PREFIX = "."

MOUSE_HELP = """
Commands: `{pre}mit`, `{pre}help`
More about me 🐭: {url}
"""

MOUSE_URL = "https://thirdwest.scripts.mit.edu/~thirdwest/wiki/index.php?title=User:Finneasj"

CATALOG_URL = "http://student.mit.edu/catalog/search.cgi?style=verbatim&when=*&termleng=4&days_offered=*&start_time=*&duration=*&total_units=*&search="
MAP_URL = "https://whereis.mit.edu/search?type=query&output=json&q="

SUBJECT_DETAILS = """
{level} ({when}) {other_icons}
Prereq: {prereq}
Units: {units}
{else}
"""

LOCATION_DETAILS = "{name} (at {street})"

MOUSE_NO_RESULTS = "I couldn't find any results for either subjects or for locations!"

LEVELS = {
   "Undergrad": "🇺",
   "Graduate":  "🇬"
}
SEASONS = {
   "Fall": "🍁",
   "Spring": "🌷",
   "IAP": "❄️",
   "Summer": "🌞"
}
OTHER_ICONS = {
   "Can be repeated for credit": "🔄",
   "Institute Lab": "🔬",
   "Rest Elec in Sci & Tech": "🇷",
   "HASS Social Sciences": "🇸",
   "HASS Arts": "🇦",
   "HASS Humanities": "🇭",
   "Communication Intensive HASS": "(CI-H)",
   "______": "🤔"
}
EMOJIS = {**LEVELS, **SEASONS, **OTHER_ICONS}

def cap_at_2000(items):
   temp = "\n".join(items)
   while len(temp) > 2000:
      del items[-1]
      temp = "\n".join(items) + "\n..."
   return temp

def url_encode(param):
   temp = ""
   for c in param:
      n = ord(c)
      if n == 32:
         temp += "+"
      elif c in "eitsanhurdmwgvlfbkopxczjyqEITSANHURDMWGVLFBKOPXCZJYQ0123456789-_.~":
         temp += c
      elif n > 32:
         temp += "%" + hex(n)[2:].upper()
   return temp

def html_to_markdown(string_):
   out = string_.replace("\n", "")
   out = out.replace("<br/>", "\n")
   out = out.replace("<i>", "*")
   out = out.replace("</i>", "*")
   out = out.replace("<b>", "**")
   out = out.replace("</b>", "**")
   return out.strip("\n ")

def find_end(string_, sub):
   i = string_.find(sub)
   return i + len(sub) if i >= 0 else i

def lcut(string_, sub, include=False):
   i = string_.find(sub) if include else find_end(string_, sub)
   return string_[i :] if i >= 0 else string_

def rcut(string_, sub, include=False):
   i = find_end(string_, sub) if include else string_.find(sub)
   return string_[: i] if i>= 0 else string_

# returns everything in string_ between left and right
def cut(string_, left, right, include=False):
   return rcut(lcut(string_, left, include), right, include)

# Returns content string, embed object, and whether there was one result
async def search_catalog(query):
   url = CATALOG_URL + url_encode(query)
   async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
         result = await response.text()
   soup = BeautifulSoup(result, "html5lib")
   embed = discord.Embed(url=url)
   embed.title = soup.body.i.get_text(strip=True).split(".")[0] + "!"
   temp = embed.title.split(" ")[0]
   if temp == "No": # No matching subjects found
      return None, None, False
   num_results = int(temp)
   if num_results > 1:
      if soup.body.blockquote.find_all("h3"): # list is reasonably short
         subjects = [h3.get_text(strip=True)for h3 in soup.body.blockquote.find_all("h3")]
      else: # list is very long but easy to parse
         subjects = [a.get_text(strip=True)for a in soup.body.blockquote.dl.find_all("a")]
      content = cap_at_2000(subjects)
   else:
      last_hline = [img for img in soup.find_all("img") if img["alt"] == "______"][-1]
      temp = "\n".join([str(sibling) for sibling in last_hline.next_siblings])
      temp = rcut(temp, "<a")
      temp = rcut(temp, "<p")
      content = html_to_markdown(temp)
      embed.title = soup.body.h3.get_text(strip=True)
      embed.url   = url
      kwargs = {"when": [], "other_icons": [], "else": ""}
      kwargs["prereq"] = cut(soup.body.blockquote.get_text(), "Prereq: ", "\n")
      kwargs["units"]  = cut(soup.body.blockquote.get_text(),  "Units: ", "\n")
      alts = [img["alt"] for img in soup.body.blockquote.find_all("img") if not img["alt"] == "______"]
      for alt in alts:
         if alt in LEVELS:
            kwargs["level"] = EMOJIS[alt]
         elif alt in SEASONS:
            kwargs["when"].append(alt + " " + EMOJIS[alt])
         else:
            kwargs["other_icons"].append(EMOJIS.get(alt, "({})".format(alt)))
      kwargs["when"] = " and ".join(kwargs["when"])
      kwargs["other_icons"] = " ".join(kwargs["other_icons"])
      embed.description = SUBJECT_DETAILS.format(**kwargs)
   return content, embed, num_results == 1

# Returns content string, embed object, and whether there was one result
async def search_map(query):
   q   = url_encode(query)
   url = MAP_URL + q
   async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
         result = json.loads(await response.text())
   if not result: # No results
      return None, None, 0
   embed = discord.Embed()
   embed.url   = "https://whereis.mit.edu/?q=" + q
   if len(result) > 1:
      embed.title = "Found {} results for location!".format(len(result))
      locations = []
      for j in result:
         locations.append(LOCATION_DETAILS.format(**j))
      content = cap_at_2000(locations)
   else:
      j = result[0]
      content = ""
      embed.description = "at {street} (`{lat_wgs84},{long_wgs84}`)".format(**j)
      embed.title = j["name"]
      embed.set_image(url=j["bldgimg"])
   return content, embed, len(result) == 1

async def get_previous_message(msg):
   # returns the message clean_content, not the message object itself
   logs = client.logs_from(msg.channel, limit=10, reverse=True)
   messages = []
   async for message in logs:
      messages.append(message)
   for m in sorted(messages, reverse=True, key=lambda m: m.timestamp):
      if m.timestamp < msg.timestamp: return m.clean_content
   return ""

client = discord.Client()

@client.event
async def on_message(msg):
   if msg.author.bot or not msg.content.startswith(MOUSE_PREFIX): return
   
   cmd, *args = msg.clean_content[len(MOUSE_PREFIX) :].split(" ")
   if cmd == "mit":
      arg = " ".join(args) if args else await get_previous_message(msg)
      c = await search_catalog(arg)
      # exactly one result for subjects
      if c[2]:
         await client.send_message(msg.channel, c[0], embed=c[1])
         return
      m = await search_map(arg)
      # exactly one result for locations
      if m[2]:
         await client.send_message(msg.channel, embed=m[1])
         return
      # No results at all
      if not any(c) and not any(m):
         await client.send_message(msg.channel, MOUSE_NO_RESULTS)
         return
      # Send both results
      if any(c): await client.send_message(msg.channel, c[0], embed=c[1])
      if any(m): await client.send_message(msg.channel, m[0], embed=m[1])

   elif cmd == "help":
      await client.send_message(msg.channel,
         MOUSE_HELP.format(pre=MOUSE_PREFIX, url=MOUSE_URL))

@client.event
async def on_error(event, *args, **kwargs):
   error = traceback.format_exc()
   error_channel = client.get_channel(os.environ["ERROR_CHANNEL"])
   embed = discord.Embed()
   embed.description = "event: {}\nargs: {}\nkwargs: {}".format(event, args, kwargs)
   await client.send_message(error_channel,
      "```\n" + error + "\n```", embed=embed)

@client.event
async def on_ready():
   print("Logged in.")

if __name__ == "__main__":
   print("Logging in...")
   client.run(os.environ["MOUSE_TOKEN"])

   print("Logged out.")
