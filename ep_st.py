#!/usr/bin/python3
#
# Inspired by code from /u/iforgot120 
#           https://www.reddit.com/user/iforgot120)
# https://www.reddit.com/r/raspberry_pi/comments/46nb99/for_my_first_project_i_made_a_display_that_takes/d08em3p
#
# Thanks to /u/rhgrant10 for lots of help as well
#           https://www.reddit.com/user/rhgrant10
# https://www.reddit.com/r/learnpython/comments/47twoy/critique_my_code_please/d0fsxh4

__author__    = '/u/scul86'
__date__      = '1 Mar 2016'
__version__   = 'v1.04'
__source__    = 'https://github.com/scul86/earthporn_showerthoughts'
__copyright__ = 'GPLv3'

import os
import praw
import random
import requests
import time
import string
import configparser
import operator

from PIL import Image
from io import BytesIO
from datetime import datetime

################################################################################
# Config file stuff
config = configparser.ConfigParser()
config.read('ep_st.config')

# Open Reddit API
r = praw.Reddit(config['DEFAULT']['appname'])

# Number of posts to get
num_posts = config['SUBREDDITS'].getint('numberposts', fallback=1000)

# Minimum size of images
min_width = config['IMAGES'].getint('minimumwidth', fallback=1920)
min_height =  config['IMAGES'].getint('minimumheight', fallback=1080)
logic = config['IMAGES'].get('logic', fallback='and')

# Paths to the files
template_path = os.path.expanduser(config['FILEPATHS']['template'])

## Temporary display file path while updating and testing
display_path = os.path.expanduser(config['FILEPATHS']['display']) 
log_path = os.path.expanduser(config['FILEPATHS']['log'])

# Frequency to refresh lists of posts.
list_refresh_rate = config['REFRESH'].getint('refreshrate', fallback=4)*60*60

image_subs = config['SUBREDDITS']['imagesubs'].split(', ')
text_subs = config['SUBREDDITS']['textsubs'].split(', ')

################################################################################

def get_posts(subs):
    """Gets the content from requested list of subs (len >= 1)
    
    :param list subs: list of subreddits to scrape posts from
    :return: list of posts in all subreddits in subs
    :rtype: list
    """
    
    posts = []
    div = len(subs)
    for sub in subs:
        s = r.get_subreddit(sub)
        p = ''
        while True: # Repeat until we don't get an error
            try:
                p = s.get_top_from_month(limit = num_posts/div)
                break # Exits the while loop once content is retrieved successfully

            # Had trouble with TypeError raised when connection is buffering too long
            # Which one would think is the same as ReadTimeout :/
            except (TypeError, ReadTimeout) as e:
                log_out('error', '{}: {}'.format(type(e).__name__, str(e)))
                
        for post in p:
            posts.append(post)
                
    return posts

def get_new_list(l):
    """Builds a n-dimensional list of posts 
    based on input list of subs on n length
    
    :param list l: list of subs to get content from
    :return: n-dimensional list of reddit posts
    :rtype: list
    """
    
    ret = []
    for i in range(0, len(l)):
        ret.append(get_posts(l[i]))
    return ret

def fix_imgur(url):
    """Given an URL, checks if it is an Imgur URL, and returns a valid
        direct Imgur URL
    
    :param str url: the url of the image to check
    :return: corrected url direct to the image
    :rtype: str
    """
    
    if 'imgur' in url and not 'i.i' in url:
        if 'https' in url:
            url =  url[0:8]+'i.'+url[8:]+'.png'       
        else: url = url[0:7]+'i.'+url[7:]+'.png'
    return url

def create_check_size(min_width, min_height, logic='and'):
    """Create a function to check the minimum size of images.

    Acceptable values for ``logic`` are 'and' or 'or'. All other values
    are silently ignored. The default is 'and'.

    :param str logic: whether one or both minimums must be met
    :param int min_width: minimum width in pixels
    :param min_height: minimum height in pixels
    :return: function that accepts a URL and returns False if the image does 
             not meet requirements.
    :rtype: function
    """
        
    # Get the right logic function. We'll use it later.
    op = operator.__and__
    if logic == 'or':
        op = operator.__or__

    # Define our custom checksize function.
    def check_size(url):
        """Given a url, return True if the image meets size requirements.

        :param str url: the url of the image to check
        :return: True if the image meets size requirements, False otherwise
        :rtype: bool
        """
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
        except (OSError, IOError) as e:
            log_out('error', '{}: {}'.format(type(e).__name__, e))
            log_out('error', 'Image URL = {}'.format(url))
            return False

        # Here's where we use the right logic.
        w, h = img.size
        return op(w >= min_width, h <= min_height)

    # Return the custom function to the caller.
    return check_size

check_size = create_check_size(min_height, min_width, logic)

def is_good_image(img_url):
    """Given an URL, determine if the url points to a file of type jpg or png,
    is greater than a desired size, and does not point to a gallery
    
    :param str url: url to determine if points to valid image
    :return: True if valid image, False otherwise
    :rtype: bool
    """
    
    return ('.jpg' in img_url[-5:] or '.png' in img_url[-5:]) and \
            check_size(img_url) and not 'gallery' in img_url

def log_out(type_out, text):
    """Writes given text to a log file
    
    :param str type_out: type of log file to write (ex: error, event, etc...)
    :param str text: text to write out to the given file
    """
    
    with open(os.path.join(log_path, type_out + '.log'), 'a') as f:
        f.write('{:%d-%b-%Y: %H:%M:%S}: {}\n'.format(datetime.now(), text))

def main():
    log_out('event', 'Script Start')

    used = []
    start_time = time.time()
    
    log_out('event', 'Getting initial list of posts')
    sfw_porn_list, shower_thought_list = get_new_list([image_subs, text_subs])
    log_out('event', 'Done')

    while True: # Repeat forever
        if time.time() - start_time > list_refresh_rate:
            log_out('event', 'Refreshing list of posts')
            sfw_porn_list, shower_thought_list = get_new_list([image_subs, text_subs])
            start_time = time.time()
            used = []
            log_out('event', 'Done')
        
        length = min(len(sfw_porn_list), len(shower_thought_list))
        
        while True: # Repeat until we get a valid image in the proper size
            i = random.randint(0, length - 1)
            img_url = fix_imgur(sfw_porn_list[i].url)
            if is_good_image(img_url) and i not in used: 
                used.append(i)            
                break
            else: pass

        witty_text = shower_thought_list[random.randint(0, length - 1)].title  # They're supposed to all be in the title

        length = len(witty_text)

        if length > 146:
            middle = int(length/2)
            split = witty_text[:middle].rfind(' ')
            witty_text = witty_text[:split]+'<br>'+witty_text[split:]

        with open(os.path.join(template_path, 'template.html'), 'r') as f: 
            template = string.Template(f.read())

        with open(os.path.join(display_path, 'ep_st.html'), 'w') as f: 
            f.write(template.substitute(img=img_url, text=witty_text))

        time.sleep(60)

if __name__ == '__main__':
	main()
