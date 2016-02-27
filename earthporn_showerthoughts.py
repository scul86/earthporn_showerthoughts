#!/usr/bin/python3
#
# Inspired by code from iforgot120 (https://www.reddit.com/user/iforgot120)
# https://www.reddit.com/r/raspberry_pi/comments/46nb99/for_my_first_project_i_made_a_display_that_takes/d08em3p

__author__    = '/u/scul86'
__date__      = '27 February 2016'
__version__   = 'v1.02'
__source__    = 'https://github.com/scul86/earthporn_showerthoughts'
__copyright__ = 'GPLv3'

import os, praw, random, requests, time, string
from PIL import Image
from io import BytesIO

r = praw.Reddit("scul86's sfwPorn Showerthoughts thing v1.0")

# Number of posts to get
getCount = 1000

# Minimum size of images
minWidth, minHeight = [1920, 1080]

# Paths to the files
template_path = '/home/[USER]/python/reddit_crawler/'
display_path = '/var/www/html/'
log_path = '/home/[USER]/.html_logs/'

# Frequency to refresh lists of posts.
hours = 4
list_refresh_time = hours*60*60

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
            break # Exits the while loop once all content is retrieved

        # Had trouble with TypeError raised when connection is buffering too long
        except (TypeError, ReadTimeout) as e:
            log_out('error', type(e).__name__ + ': ' + str(e))

    return [[sub for sub in earthContent] + \
           [sub for sub in skyContent] + \
           [sub for sub in lakeContent] + \
           [sub for sub in ruralContent] + \
           [sub for sub in spaceContent], \
           [sub for sub in showerContent]]

def fix_imgur(url):
    # Some posts would lead to an imgur page link, rather than a direct link to the image
    # This converts the page link to the direct link
    if 'imgur' in url and not 'i.i' in url:
        if 'https' in url:
            url =  url[0:8]+'i.'+url[8:]+'.png'       
        else: url = url[0:7]+'i.'+url[7:]+'.png'
    return url

def good_image(imgURL):
    return (".jpg" in imgURL[-5:] or ".png" in imgURL[-5:]) and \
            checksize(imgURL) and not 'gallery' in imgURL

def checksize(imgURL):
    try: 
        response = requests.get(imgURL)
        img = Image.open(BytesIO(response.content))
    except (OSError, IOError) as e:
        log_out('error', type(e).__name__ + ': ' + str(e))
        log_out('error', 'ImgURL = ' + imgURL)
        return False

    w, h = img.size

    return (w >= minWidth and h >= minHeight)

def log_out(type_out, text):
    now = time.strftime('%d-%b-%Y: %H:%M:%S')
    with open(os.path.join(log_path, type_out + '.log'), 'a') as f:
        f.write(now + ': ' + text +'\n')

def main():
    log_out('event', 'Script Start')

    used = []
    start_time = time.time()
    
    log_out('event', 'Getting initial list of posts')
    sfwpornList, showerthoughtList = get_new_list()
    log_out('event', 'Done')

    while True: # Repeat forever
        if time.time() - start_time > list_refresh_time:
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
            if good_image(imgURL) and i not in used: 
                used.append(i)            
                break
            else: pass

        wittyText = showerthoughtList[random.randint(0, length - 1)].title  # They're supposed to all be in the title

        length = len(wittyText)

        if length > 146:
            middle = int(length/2)
            split = wittyText[:middle].rfind(' ')
            wittyText = wittyText[:split]+'<br>'+wittyText[split:]

        with open(os.path.join(template_path, 'template.html'), 'r') as f: 
            template = string.Template(f.read())

        with open(os.path.join(display_path, 'ep_st.html'), 'w') as f: 
            f.write(template.substitute(img=imgURL, text=wittyText))

        time.sleep(60)

if __name__ == '__main__':
	main()
