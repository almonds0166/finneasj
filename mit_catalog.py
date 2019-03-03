
# Note: This module was modified from the original to add "sqeaks" for
#       example shark person's personality.

import aiohttp
import re
from random import randint # esp

CATALOG_URL = "http://student.mit.edu/catalog/search.cgi?style=verbatim&when=*&termleng=4&days_offered=*&start_time=*&duration=*&total_units=*&search="

def url_encode(s):
   temp = ""
   for c in s:
      n = ord(c)
      if n == 32:
         temp += "+"
      elif c in "eitsanhurdmwgvlfbkopxczjyqEITSANHURDMWGVLFBKOPXCZJYQ0123456789-_.~":
         temp += c
      elif n > 32:
         temp += "%" + hex(n)[2:].upper()
   return temp

def search_campus(query):
   temp = " ".join(add_more_squeaks("This map may help".split(" ")))
   return "https://whereis.mit.edu/?q=" + url_encode(query), None, "https://i.imgur.com/TtLgMbQ.jpg", temp

def cap_at_2000(ell):
   content = "\n".join(ell)
   while len(content) > 2000:
      del ell[-1]
      content = "\n".join(ell) + "\n..."
   return content

def add_more_squeaks(in_):
   out = in_.copy()
   squeaks = 0
   while squeaks < min(10, max(0, randint(-2, 1 + len(out) // 3))):
      squeaks += 1
      out.insert(randint(0, len(out)), "\\*squeak\\*")
   return out

time_emoji = {
   "Fall": "🍁",
   "Spring": "🌷",
   "IAP": "❄️",
   "Summer": "🌞"
}

async def search_subject(query):
   search_url = CATALOG_URL + url_encode(query)
   async with aiohttp.ClientSession() as session:
      async with session.get(search_url) as response:
         result = await response.text()
         i = result.find("<BR><P><I>") + 10
         j = result.find("</I>", i)
         num_results = result[i : j].split(" ")[0]
         if num_results == "No": # no results
            return None, "No results found 🤔", search_url, None
         i = result.find("<DL>", j) + 4
         subjects = []
         if i >= 4: # many classes
            j = result.find("</DL>", i)
            raw_results = result[i : j].strip("\n").replace("\n\n", "\n")
            for line in raw_results.split("\n"):
               temp = line.replace("<DT><A HREF=\"", "")
               temp = temp.replace("</A>", "")
               temp = temp.replace("<br>", " ")
               temp = temp.split("\">")
               title = temp[1]
               i = title.find("<DD>")
               if i >= 0:
                  title = title[: i]
               number, title = title.split(" ", 1)
               subjects.append("**" + number + "**: " + title)
            subjects = add_more_squeaks(subjects) # esp
            return cap_at_2000(subjects), num_results + " results", search_url, None
         else:
            i = result.find("<P>", j) + 3
            j = result.find("</blockquote>", i)
            raw_results = result[i : j].strip("\n")
            i = 7
            if int(num_results) > 1:
               for raw in raw_results.split("<!--end-->")[: -1]:
                  j = raw.find("\n", 8)
                  number, title = raw[i : j].split(" ", 1)
                  subjects.append("**" + number + "**: " + title)
                  i = 8
               subjects = add_more_squeaks(subjects) # esp
               return cap_at_2000(subjects), num_results + " results", search_url, None
            else:
               raw = raw_results
               j = raw.find("\n", 8)
               number, title = raw[7 : j].split(" ", 1)
               i = raw.find("Prereq:") + 8
               j = raw.find("\n", i)
               prereq = raw[i : j]
               prereq = re.sub(r"[\<].*?[\>]", "", prereq)
               i = raw.find("Units:") + 7
               if i >= 7:
                  j = raw.find("\n", i)
                  units = raw[i : j]
                  units += " ({})".format(sum([int(n) for n in units.split("-")]))
               else:
                  units = "Arranged"
               alts = set()
               for item in ["first half of term", "second half of term", "Not offered regularly; consult department"]:
                  if item in raw:
                     alts.add(item)
               i = raw.find("title=\"") + 7
               while i >= 7:
                  j = raw.find("\"", i)
                  alts.add(raw[i : j])
                  i = raw.find("title=\"", j) + 7
               when = set()
               for time in ["Fall", "Spring", "Summer", "IAP"]:
                  if time in alts:
                     when.add(time + " " + time_emoji[time])
                     alts.remove(time)
               hass = set()
               for flavor in ["HASS Humanities", "HASS Arts", "HASS Elective", "HASS Social Sciences", "HASS Humanities", "Communication Intensive HASS", "Communication Intensive Writing"]:
                  if flavor in alts:
                     hass.add(flavor)
                     alts.remove(flavor)
               i = raw.rfind("src=\"/icns/hr.gif\">\n<br>")
               i += 24
               j = raw.find("\n<br>", i)
               description = raw[i : j]
               description = " ".join(add_more_squeaks(description.split(" "))) # esp
               return description, \
                  number + ": " + title, \
                  search_url, \
                  " and ".join(when) + "\n" + \
                  "Units: " + units + "\n" + \
                  "Prereq: " + prereq + "\n" + \
                  ("" if not hass else ("HASS: " + ", ".join([item.replace("HASS ", "") for item in hass])))

MIT_LANDMARKS = ["great dome", "the dome", "killian", "walker", "senior house",
   "baker", "hayden", "chapel", "kresge", "dupont", "mccormick", "east campus",
   "dreyfus", "burton connor", "simmon", "jonhson", "z center", "z-center",
   "athletic center", "stata", "mit.nano", "lobby", "cafe"]

async def mit_search(query):
   if "[j]" in query.lower(): return await search_subject(query)
   if query.isdigit() or any(word in query.lower() for word in MIT_LANDMARKS):
      return search_campus(query)
   if query.count(" "):
      if any([query.lower().startswith(word) for word in \
         ["building ", "bldg ", "bldg. ", "room ", "classroom "]]):
         return search_campus(query)
      return await search_subject(query)
   if "-" in query or query.isalnum() and query[-1].isdigit() and not "." in query: 
      return search_campus(query)
   return await search_subject(query)

