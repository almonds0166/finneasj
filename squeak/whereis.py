
import asyncio
from urllib.parse import urlencode, quote
import json

import discord
import aiohttp

from .util import cap_at_n, SearchResults

HEADERS = {"User-Agent": "finneasj/1.0"}

# Returns content string, embed object, and whether there was one result
async def search(query, debug=False):
   q = urlencode({"q": query}, quote_via=quote)
   url = "https://whereis.mit.edu/search?type=query&output=json&{}".format(q)

   async with aiohttp.ClientSession() as session:
      async with session.get(url, headers=HEADERS) as response:
         result = json.loads(await response.text())

   if debug: print(result)

   if not result: # No results
      return SearchResults("", None, 0)

   # prepare bot message
   embed = discord.Embed()
   embed.url = "https://whereis.mit.edu/?{}".format(q)
   content = ""

   # unpack http response
   if len(result) > 1:
      embed.title = "Found {} location results!".format(len(result))
      locations = []
      for location in result:
         if all(k in location for k in ("bldgnum", "street")):
            locations.append("{name} ({bldgnum}, at {street})".format(**location))
         else:
            locations.append(location["name"])
      embed.description = cap_at_n(locations, 500)
   else:
      location = result[0]
      embed.description = "(`{lat_wgs84},{long_wgs84}`)".format(**location)
      if all(k in location for k in ("bldgnum", "street")):
         embed.description = "Building {bldgnum}\n{street} ".format(**location) + embed.description
      embed.title = location["name"]
      if "bldgimg" in location:
         embed.set_image(url=location["bldgimg"])

   return SearchResults(content, embed, len(result))

if __name__ == "__main__":
   print("Give me a map query.")
   try:
      while True:
         q = input("> ")
         content, embed, num_results = asyncio.run(search(q, debug=True))
         print("Content")
         print("=======")
         print(content)
         print()
         print("Embed")
         print("=====")
         if embed:
            print("title:", embed.title)
            print("url:", embed.url)
            print("description:", embed.description)
            print("image url:", embed.image.url)
         else:
            print(embed)
         print()
         print("Results:", num_results)
         print()
   except KeyboardInterrupt:
      print("^C")