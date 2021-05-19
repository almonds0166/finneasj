
# shared helper functions go here
def cap_at_n(lines, n=2000):
   """
   Takes in a list of strings and joins them with `\n`, but no more than n
   characters. The Discord message character limit is 2000.
   """
   text = ""
   for line in lines:
      if len(text) + len(line) + 1 < n - 3:
         text += line + "\n"
      else:
         text += "..."
         break
   return text

def html_to_md(html):
   """
   Lazy method to convert any happenstance HTML to Discord markdown.
   Specifically just bold and italics.
   I'm not actually sure if this is needed.
   """
   md = html.replace("<i>", "*")
   md = md.replace("</i>", "*")
   md = md.replace("<b>", "**")
   md = md.replace("</b>", "**")
   return md.strip("\n ")

def squeakify(obj):
   """
   I'm not ready yet
   Let me clean the living room
   Then you can come back
   """
   pass

class SearchResults:
   """
   Simple wrapper that represents a search result
   """
   def __init__(self, content, embed, num_results):
      self.content = content
      self.embed = embed
      self.num_results = num_results