#!/usr/bin/python3
#
# Based on code by iforgot120 (https://www.reddit.com/user/iforgot120)
# https://www.reddit.com/r/raspberry_pi/comments/46nb99/for_my_first_project_i_made_a_display_that_takes/d08em3p

import os, praw, random, requests, time, string
from PIL import Image
from io import BytesIO

r = praw.Reddit("scul86's sfwPorn Showerthoughts thing v1.0")

getCount = 1000
screenWidth, screenHeight = [1920, 1080]

def get_new_list():
    earthSub = r.get_subreddit('earthporn')
    skySub = r.get_subreddit('skyporn')
    lakeSub = r.get_subreddit('lakePorn')
    ruralSub = r.get_subreddit('ruralporn')
    spaceSub = r.get_subreddit('spaceporn')
    
    showerSub = r.get_subreddit('showerthoughts')

    while True: # Repeat if we get an error
        try:
            earthContent = earthSub.get_top_from_month(limit = getCount/5)
            skyContent = skySub.get_top_from_month(limit = getCount/5)
            lakeContent = lakeSub.get_top_from_month(limit = getCount/5)
            ruralContent = ruralSub.get_top_from_month(limit = getCount/5)
            spaceContent = spaceSub.get_top_from_month(limit = getCount/5)
            showerContent = showerSub.get_top_from_month(limit = getCount)
            break

        # Had trouble with TypeError raised when connection is buffering too long
        except TypeError as detail:
            log_out('error', 'TypeError: ' + detail)

    return [[sub for sub in earthContent] + \
           [sub for sub in skyContent] + \
           [sub for sub in lakeContent] + \
           [sub for sub in ruralContent], \
           [sub for sub in showerContent]]

def fix_imgur(url):
    if "imgur" in url and not "i.i" in url:
        if "https" in url:
            url =  url[0:8]+'i.'+url[8:]+'.png'       
        else: url = url[0:7]+'i.'+url[7:]+'.png'
    return url

def good_image(imgURL):
    return (".jpg" in imgURL or ".png" in imgURL) and checksize(imgURL)

def checksize(imgURL):
    try: response = requests.get(imgURL)
    except OSError as detail:
        log_out('error', 'OSError: ' + details)
        return False
    img = Image.open(BytesIO(response.content))
    w, h = img.size

    return (w >= screenWidth and h >= screenHeight)

def log_out(type_out, text):
    now = time.strftime('%d-%b-%Y: %H:%M:%S')
    with open(type_out+'.log', 'a') as f:
        f.write(now + ': ' + text +'\n')

log_out('event', 'Script Start')

used = []
start_time = time.time()

log_out('event', 'Getting initial list of posts')
sfwpornList, showerthoughtList = get_new_list()
log_out('event', 'Done')

while True: # Repeat forever
    if time.time() - start_time > 60*60: # Refresh the lists every hour
        log_out('event', 'Refreshing list of posts')
        sfwpornList, showerthoughtList = get_new_list()
        start_time = time.time()
        used = []
        log_out('event', 'Done')
    
    length = len(sfwpornList)
    if length > len(showerthoughtList):
        length = len(showerthoughtList)
    
    while True: # Repeat until we get a valid image in the proper size
        i = random.randint(0, length - 1)
        imgURL = fix_imgur(sfwpornList[i].url)
        #print('\n' + sfwpornList[i].title + '\n' + imgURL)
        if good_image(imgURL) and i not in used: 
            used.append(i)            
            break
        else: pass

    wittyText = showerthoughtList[random.randint(0, length - 1)].title  # They're typically supposed to be all in the title
    
    #print(wittyText)

    length = len(wittyText)

    if length > 146:
        middle = int(length/2)
        split = wittyText[:middle].rfind(' ')
        wittyText = wittyText[:split]+'<br>'+wittyText[split:]
    
    with open('/home/kyle/python/reddit_crawler/template.html', 'r') as f: 
        template = string.Template(f.read())

    with open('/home/kyle/python/reddit_crawler/display.html', 'w') as f: 
        f.write(template.substitute(img=imgURL, text=wittyText))

    time.sleep(60)
