#!/usr/bin/python3
#
# Based on code by iforgot120 (https://www.reddit.com/user/iforgot120)
# https://www.reddit.com/r/raspberry_pi/comments/46nb99/for_my_first_project_i_made_a_display_that_takes/d08em3p

import os, praw, random, requests, time, string, re
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
            print("TypeError: " + detail)

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
    # I had a sweet regex expression to get the image size from the post title
    # Then I discovered Pillow/PIL
    # '[0-9]+ *[xX×] *[0-9]+'
    response = requests.get(imgURL)
    img = Image.open(BytesIO(response.content))
    w, h = img.size
    print(img.size)

    return (w > 1920 and h > 1080)

used = []
start_time = time.time()
sfwpornList, showerthoughtList = get_new_list()

while True: # Repeat forever
    if time.time() - start_time > 60*60: # Refresh the lists every hour
        sfwpornList, showerthoughtList = get_new_list()
        start_time = time.time()
        used = []
        print("Refreshing the list of posts")
    
    length = len(sfwpornList)
    if length > len(showerthoughtList):
        length = len(showerthoughtList)
    
    while True: # Repeat until we get a valid image in the proper size
        i = random.randint(0, length - 1)
        imgURL = fix_imgur(sfwpornList[i].url)
        print('\n' + sfwpornList[i].title + '\n' + imgURL)
        if good_image(imgURL) and i not in used: 
            used.append(i)            
            break
        else: print("Selecting another")

    wittyText = showerthoughtList[random.randint(0, length - 1)].title  # They're typically supposed to be all in the title
    
    #print(wittyText)
    
    with open('/home/kyle/python/reddit_crawler/template.html', 'r') as f: 
        template = string.Template(f.read())

    with open('/home/kyle/python/reddit_crawler/display.html', 'w') as f: 
        f.write(template.substitute(img=imgURL, text=wittyText))

    time.sleep(60)
