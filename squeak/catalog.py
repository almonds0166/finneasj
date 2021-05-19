
import asyncio
from urllib.parse import urlencode, quote

import discord
import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Tag

from .util import cap_at_n, html_to_md, SearchResults

HEADERS = {"User-Agent": "finneasj/1.0"}

CATALOG_URL = "http://student.mit.edu/catalog/search.cgi?style=verbatim&when=*&termleng=4&days_offered=*&start_time=*&duration=*&total_units=*&{}"

# to replace symbols used in the catalog with emojis
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
   "Not offered academic year 2021-2022": "🚫"
}

# Returns content string, embed object, and whether there was one result
async def search(query, style="verbatim", debug=False):
   params = {
      "style": style if style != "all" else "any",
      "search": query
   }
   url = CATALOG_URL.format(urlencode(params, quote_via=quote))

   async with aiohttp.ClientSession() as session:
      async with session.get(url, headers=HEADERS) as response:
         result = await response.text()

   soup = BeautifulSoup(result, "html5lib")

   if debug: print(soup)

   summary = soup.body.i.get_text(strip=True) # summary of results
   summary = summary.split(".")[0] + "!" # take first sentence

   # prepare bot message
   embed = discord.Embed(url=url)
   embed.title = summary
   content = ""

   num_results = summary.split(" ")[0]
   if num_results == "No": # No matching subjects found
      return SearchResults("", None, 0)
   else:
      num_results = int(num_results)

   if num_results > 1:
      h3_headers = soup.body.blockquote.find_all("h3")
      if h3_headers: # results list is short
         subjects = [h3.get_text(strip=True) for h3 in h3_headers]
      else: # results list is medium or long
         subjects = [a.get_text(strip=True) for a in soup.body.blockquote.dl.find_all("a")]

      embed.description = cap_at_n(subjects, 500)

   else: # a single result!
      # the description is found just underneath the last horizontal line on the page
      description = ""
      staff = []
      last_hline = [img for img in soup.find_all("img") if img["alt"] == "______"][-1]
      for sibling in last_hline.next_siblings:
         if sibling.string and not description:
            description = html_to_md(str(sibling)) # subject description
         elif isinstance(sibling, Tag) and sibling.name == "i": # Staff
            if sibling.string not in staff: staff.append(sibling.string)
      if staff:
         staff = ", ".join(f"*{s}*" for s in staff)
      # subject title
      embed.title = soup.body.h3.get_text(strip=True)
      # parse the high-level details
      flag = False
      details = ""
      units = ""
      total_units = 0
      prereqs = ""
      for line in soup.body.blockquote.get_text().split("\n"):
         line = line.strip()
         if not flag:
            if any(line.startswith(x) for x in ("()", "(, )", "(, , )", "(, , , )")):
               flag = True
               line = line[line.index(")")+1:]
               if not line: continue
         if flag:
            if line == "": # end of details
               break
            if line.startswith("Units"):
               units = line
               try:
                  total_units = sum(int(u) for u in units.split(" ")[1].split("-"))
               except ValueError:
                  pass
               if total_units > 1:
                  units = units + f" ({total_units} total)"
               if units.startswith("Units: "):
                  units = units[7:]
            elif line.startswith("Prereq"):
               prereqs = line
               if prereqs.startswith("Prereq: "):
                  prereqs = prereqs[8:]
            else:
               details += "\n" + line
      details = details[1:] # cut off left `\n`
      details = details.replace(")(", ")\n(") # cheap fix
      # parse the icons into undergrad/grad, season, and any others
      level = "?"
      seasons = []
      other = []
      for sibling in soup.body.find("h3").next_siblings:
         if isinstance(sibling, Tag) and sibling.name == "img":
            if sibling.get("alt") == "______":
               break
            else:
               img = sibling.get("alt", "")
               if img in LEVELS:
                  level = LEVELS[img]
               elif img in SEASONS:
                  seasons.append(f"{img} {SEASONS[img]}")
               elif img in OTHER_ICONS:
                  other.append(OTHER_ICONS[img])
               else:
                  other.append(f"({img})")
      seasons = ", ".join(seasons)
      other = " ".join(other)

      # OK, cool, at this point, we should have undergrad/grad, when the class
      # takes place, other icons, and course description + staff
      embed.description = (
         f"{level} ({seasons}) {other}\n"
         f"{details}"
      )
      embed.add_field(
         name="Prereq",
         value=prereqs,
         inline=True
      )
      embed.add_field(
         name="Units",
         value=units,
         inline=True
      )
      if staff:
         embed.add_field(
            name="Staff",
            value=staff,
            inline=True
         )
      embed.add_field(
         name="Description",
         value=description,
         inline=False
      )

   return SearchResults(content, embed, num_results)

if __name__ == "__main__":
   print("Give me a catalog query.")
   try:
      while True:
         q = input("> ")
         r = asyncio.run(search(q, debug=True)); break
         print("Content")
         print("=======")
         print(r.content)
         print()
         print("Embed")
         print("=====")
         if r.embed:
            print("title:", r.embed.title)
            print("url:", r.embed.url)
            print("description:", r.embed.description)
            print("field[0]:", r.embed.fields[0].value)
            print("field[1]:", r.embed.fields[1].value)
            print("field[2]:", r.embed.fields[2].value)
            if len(r.embed.fields) > 3: print("field[3]:", r.embed.fields[3].value)
         else:
            print(r.embed)
         print()
         print("Results:", r.num_results)
         print()
   except KeyboardInterrupt:
      print("^C")