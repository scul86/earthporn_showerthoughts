#!/usr/bin/python3
#
# Based on code by iforgot120 (https://www.reddit.com/user/iforgot120)
# https://www.reddit.com/r/raspberry_pi/comments/46nb99/for_my_first_project_i_made_a_display_that_takes/d08em3p

import os, praw, random, requests, time, string, re

r = praw.Reddit("scul86's sfwPorn Showerthoughts thing v1.0")

getCount = 1000
screenWidth, screenHeight = [1920, 1080]

def get_new_list():
    earthpornSub = r.get_subreddit('earthporn')
    skypornSub = r.get_subreddit('skyporn')
    lakepornSub = r.get_subreddit('lakePorn')
    ruralpornSub = r.get_subreddit('ruralporn')
    spacepornSub = r.get_subreddit('spaceporn')
    
    showerthoughtSub = r.get_subreddit('showerthoughts')

    while True:
        try:
            earthpornContent = earthpornSub.get_top_from_month(limit = getCount/5)
            skypornContent = skypornSub.get_top_from_month(limit = getCount/5)
            lakepornContent = lakepornSub.get_top_from_month(limit = getCount/5)
            ruralpornContent = ruralpornSub.get_top_from_month(limit = getCount/5)
            spacepornContent = spacepornSub.get_top_from_month(limit = getCount/5)
            
            showerthoughtContent = showerthoughtSub.get_top_from_month(limit = getCount)
            break

        except TypeError as detail: 
        # Had trouble with TypeError raised when connection is buffering too long
            print("TypeError: " + detail)

    return [[sub for sub in skypornContent] + \
           [sub for sub in skypornContent] + \
           [sub for sub in lakepornContent] + \
           [sub for sub in ruralpornContent], \
           [sub for sub in showerthoughtContent]]

def fix_imgur(url):
    if "imgur" in url and not "i.i" in url:
        if "https" in url:
            url =  url[0:8]+'i.'+url[8:]+'.png'       
        else: url = url[0:7]+'i.'+url[7:]+'.png'
    return url

def good_image(post):
    imgURL = fix_imgur(post.url)
    return (".jpg" in imgURL or ".png" in imgURL) and checksize(post.title)

def checksize(title): 
    # Any way to check size based on the actual image without downloading it?
    m = re.search('[0-9]+ *[xX] *[0-9]+', title)
    try:
        w, h = m.group().replace(' ', '').lower().split('x')
    except AttributeError:
        print("Can't determine size")
        return False
    return (int(w) > 1920 and int(h) > 1080)

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
        if good_image(sfwpornList[i]) and i not in used: 
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
