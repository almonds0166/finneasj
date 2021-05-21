# Finneas Jawsen documentation

Discord bot that can retrieve information about MIT subjects and locations.

Somewhat inspired by [DuckDuckGo's `!mit` bang](https://duckduckgo.com/bang?q=mit).

# Commands

| Command, usage | Effect                                                       |
| :------------: | ------------------------------------------------------------ |
|     `.mit`     | Prints help message.                                         |
| `.mit <query>` | Search [MIT's Subject Listing & Schedule](http://student.mit.edu/catalog/index.cgi) (hereafter, "the catalog") for the given query as an exact phrase in the title or description. |
| `.map <query>` | Provide a link to [whereis.mit.edu](https://whereis.mit.edu) that searches for the given query. |

Queries are always case-insensitive.

## Slash commands

Note as of 19 May 2021: The prefixed commands above will be replaced with the [slash commands](https://blog.discord.com/slash-commands-are-here-8db0a385d9e6) below, when [discord.py](https://discordpy.readthedocs.io/en/stable/#) gets around to implementing slash commands into their wrapper, followed by when I get around to implementing discord.py's slash commands into finneasj.

|        Command, usage        | Effect                                                       |
| :--------------------------: | ------------------------------------------------------------ |
|          `/squeak`           | Prints help message.                                         |
|      `/subject <query>`      | Search the catalog for the given query *as an exact phrase*. |
| `/subject professor <query>` | Search the catalog for subjects taught by the given query *as a professor's last name*. |
|  `/subject prereq <query>`   | Search the catalog for subjects that have the given query *as a prerequisite or corequisite*. |
|    `/subject all <query>`    | Search the catalog for subjects *with all of the words* in the given query. |
|      `/whereis <query>`      | Provide a link to whereis.mit.edu that searches for the given query. |

# Environment variables

To run the bot, export the following environment variables:

* `MOUSE_TOKEN`: the bot token
* `MOUSE_PREFIX`: the bot prefix
* `ERROR_CHANNEL` (optional): ID of the channel to send error messages to

# How it works

## Catalog search

Finneas uses [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to read [the MIT subject catalog](http://student.mit.edu/catalog/index.cgi). MIT does have [some APIs](https://ist.mit.edu/apis), and I did try to use [the Subjects one](https://developer.mit.edu/apis-subjects) a while back, but I couldn't actually get it to work, and Beautiful Soup works well enough. Maybe in the future, if someone wants to build upon this project, they can look into these APIs and augment Finneas if they turn out to be useful enough.

### Advanced search

Advanced search refers to the `/subject professor`, `/subject prereq`, and `/subject all` commands. They match the options available on [the advanced search page of the MIT subject listing](http://student.mit.edu/catalog/extsearch.cgi). The URL query parameters that correspond to these options are, respectively:

* `style=verbatim`: exact phrase, corresponding to the `/subject`
* `style=professor`: professor last name, corresponding to `/subject professor`
* `style=prereq`: prereq/coreq, corresponding to `/subject prereq`
* `style=any`: all words appear in description, corresponding to `/subject all`

The `any` style searches for classes with descriptions that contains *all* the desired words. Due to this discrepancy, I suspect the `any` style might have originally been planned to search for classes with descriptions that contain *any* of the desired words. Ultimately, I decided it would be more intuitive to specify this search style through Finneas using the word "all" instead of "any".

### Search cases

There are roughly five kinds of results that the search catalog can return. Debugging/testing should at the very least test each of these cases.

1. No results (example: [`!mit blahblahblah`](http://student.mit.edu/catalog/search.cgi?search=blahblahblah))
2. Exactly one result (example: [`!mit 6.034`](http://student.mit.edu/catalog/search.cgi?search=6.034))
3. Short list of results (about ten) (example: [`!mit language processing`](http://student.mit.edu/catalog/search.cgi?search=language%20processing))
4. Medium list of results ([`!mit embedded`](http://student.mit.edu/catalog/search.cgi?search=embedded))
5. Long list of results (example: [`!mit electronics`](http://student.mit.edu/catalog/search.cgi?search=electronics))

Click the links to view each example, in order to get a feel for how Finneas reads the HTML differently in these cases.

Finneas takes advantage of how for each of these pages, the number of results may always be found as the first italicized element in the webpage's HTML body. The zero results case is easily detected by reading "*No results found*."

Similarly, for exacly one result, the first italicized element will read "*1 subject found.*" The subject is then carefully formatted into a Discord message embed, given the HTML soup. For instance, the subject title is the `h3` header tag. High-level subject details are found after a horizontal line that corresponds to an `img` element with a consistent `alt` attribute. Other `img` elements carry information such as whether the subject is for undergrad vs. grad and which semester(s) it's offered. The prerequisites and units are also found here. After another horizontal line comes the subject description and potentially the staff if they've filled that information in.

In the third case for a short list of results, the subject titles are encoded in all the `h3` headers.

In the fourth and fifth cases for longer lists, the anchors within the body's blockquote's description list element (`dl`) encode the class names.

## Map search

This "API" was found by observing the Ajax on [`whereis.mit.edu`](https://whereis.mit.edu/), specifically `https://whereis.mit.edu/search` using query parameters `type=query`, `output=json`, and `q` for the query. The objects *tend* to have the following keys, though not all do (for instance, `q=ihtfp`):

* `bldgimg`: URL to an image representing the place
* `bldgnum`: The building number
* `lat_wgs84` and `long_wgs84`: latitude and longitude
* `name`: The name of the place
* `street`: The street location

Finneas uses these elements to construct his messages. 