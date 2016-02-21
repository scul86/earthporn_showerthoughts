#!/usr/bin/python3
# https://www.reddit.com/r/raspberry_pi/comments/46nb99/for_my_first_project_i_made_a_display_that_takes/d08em3p

import os, praw, random, requests, time, string

def fix_imgur(url):
    if "imgur" in url and not "i.i" in url:
        return url[0:7]+'i.'+url[7:]+'.png'
    return url

r = praw.Reddit("iforgot120's Earthporn Showerthoughts thing v1")
getCount = 500

while True:
    earthpornSub = r.get_subreddit('earthporn')
    showerthoughtSub = r.get_subreddit('showerthoughts')

    earthpornContent = earthpornSub.get_top_from_month(limit = getCount)
    showerthoughtContent = showerthoughtSub.get_top_from_month(limit = getCount)

    earthpornList = [sub for sub in earthpornContent]
    showerthoughtList = [sub for sub in showerthoughtContent]
    
    length = len(earthpornList)
    
    if length > len(showerthoughtList):
        length = len(showerthoughtList)

    imgURL = fix_imgur(earthpornList[random.randint(0, length - 1)].url)
    wittyText = showerthoughtList[random.randint(0, length - 1)].title  # They're typically supposed to be all in the title
    
    print(imgURL)
    print(wittyText)
    
    with open('/home/kyle/python/reddit_crawler/template.html', 'r') as f: template = string.Template(f.read())
    with open('/home/kyle/python/reddit_crawler/display.html', 'w') as f: f.write(template.substitute(img=imgURL, text=wittyText))

    time.sleep(60)
