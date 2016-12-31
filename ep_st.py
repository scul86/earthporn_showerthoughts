#!venv/bin/python3
#
# Inspired by code from /u/iforgot120 
#           https://www.reddit.com/user/iforgot120)
# https://www.reddit.com/r/raspberry_pi/comments/46nb99/for_my_first_project_i_made_a_display_that_takes/d08em3p
#
# Thanks to /u/rhgrant10 for lots of help as well
#           https://www.reddit.com/user/rhgrant10
# https://www.reddit.com/r/learnpython/comments/47twoy/critique_my_code_please/d0fsxh4

__author__ = '/u/scul86'
__date__ = '3 Dec 2016'
__version__ = 'v1.06'
__source__ = 'https://github.com/scul86/earthporn_showerthoughts'
__copyright__ = 'GPLv3'

import os
import praw
import random
import requests
import time
import string
import configparser
import argparse
import operator
import logging

from PIL import Image
from io import BytesIO
from imgurpython import ImgurClient
from multiprocessing import Pool

################################################################################
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--level')
args = parser.parse_args()
level = args.level

# Config file stuff
config = configparser.ConfigParser()
config.read('ep_st.config')

# Open Reddit API
r = praw.Reddit(config['DEFAULT']['appname'])

# imgur API
imgur_id = config['IMGUR'].get('id')
imgur_secret = config['IMGUR'].get('secret')
imgur_client = ImgurClient(imgur_id, imgur_secret)

# Number of posts to get
num_posts = config['SUBREDDITS'].getint('numberposts', fallback=1000)

# Minimum size of images
min_width = config['IMAGES'].getint('minimumwidth', fallback=1920)
min_height = config['IMAGES'].getint('minimumheight', fallback=1080)
logic = config['IMAGES'].get('logic', fallback='and')

# Paths to the files
template_path = os.path.expanduser(config['FILEPATHS']['template'])

# Temporary display file path while updating and testing
display_path = os.path.expanduser(config['FILEPATHS']['display'])
log_path = os.path.expanduser(config['FILEPATHS']['log'])

# print(log_path)

# Frequency to refresh lists of posts.
list_refresh_rate = config['REFRESH'].getint('refreshrate', fallback=4) * 60 * 60

image_subs = config['SUBREDDITS']['imagesubs'].split(', ')
text_subs = config['SUBREDDITS']['textsubs'].split(', ')

# logging config
logging.basicConfig(filename=os.path.join(log_path,'ep_st.log'),
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
log_levels = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warn': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

if not level:  # if logging level was not set with an argument
    level = config['LOGGING']['level'].lower()

try:
    logger.setLevel(log_levels[level])
except KeyError:
    logger.setLevel(logging.INFO)
    logger.error('Invalid logging level, log level set to INFO')
    logger.info("Valid values are 'debug', 'info', 'warn', 'error', or 'critical'")

logger.debug("Logging configuration complete")
################################################################################


def get_posts(sub):
    """Gets the content from requested subreddit (len >= 1)
    
    :param str sub: subreddit to scrape posts from
    :return: list of posts in given subs
    :rtype: list
    """

    logger.info('Getting posts from sub: {}'.format(sub))
    s = r.get_subreddit(sub)
    while True:  # Repeat until we don't get an error
        try:
            p = s.get_top_from_month(limit=num_posts)
            break  # Exits the while loop once content is retrieved successfully

        # Had trouble with TypeError raised when connection is buffering too long
        # Which one would think is the same as ReadTimeout :/
        except (TypeError, ReadTimeout) as e:
            logger.error('{}: {}'.format(type(e).__name__, str(e)))

    return list(p)


def get_new_list(l):
    """Builds a list of posts
    based on input list of subs
    
    :param list l: list of subs to get content from
    :return: list of Reddit posts
    :rtype: list
    """

    logger.info('Getting new list of posts')
    start_time = time.time()

    p = Pool(processes=len(l))
    data = p.map(get_posts, l)
    p.close()

    # p.map returns 2D list, return for this function needs to be 1D
    #     the code below flattens it.
    ret = [item for sublist in data for item in sublist]

    end_time = time.time()
    logger.info('Finished in {0:.2f} seconds'.format(end_time - start_time))
    return ret


def get_album_image(url):
    """Given an imgur album URL, returns a valid direct
            Imgur URL to a random image in the album

        :param str url: the url of the album
        :return: url direct to the image
        :rtype: str
        """
    logger.info('Expanding imgur album.  URL: {}'.format(url))
    album_id = url.split('/')[-1]
    images = imgur_client.get_album_images(album_id=album_id)
    return random.choice(images).link


# def get_gallery_image(url):
    ''' """Given an imgur gallery URL, returns a valid direct
            Imgur URL to a random image in the gallery

        :param str url: the url of the gallery
        :return: url direct to the image
        :rtype: str
        """

    gallery_id = url.split('/')[-1]
    images = imgur_client.get_custom_gallery(gallery_id=gallery_id)
    return random.choice(images).link'''


def fix_imgur(img_url):
    """Given an URL, checks if it is an Imgur URL, and returns a valid
        direct Imgur URL
    
    :param str img_url: the url of the image to check
    :return: corrected url direct to the image
    :rtype: str
    """

    # logger.debug('URL is: {}'.format(img_url))
    if '?' in img_url and 'imgur' in img_url:
        img_url = img_url.split('?')[0]

    if 'imgur.com/a/' in img_url:
        return get_album_image(img_url)
    # elif 'imgur.com/gallery/' in url:
    #    return get_gallery_image(url)'''
    elif 'imgur' in img_url and not 'i.i' in img_url and not 'iob.i' in img_url:
        if 'https' in img_url:
            img_url = img_url[0:8] + 'i.' + img_url[8:] + '.png'
        else:
            img_url = img_url[0:7] + 'i.' + img_url[7:] + '.png'
    return img_url


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
    def check_size_inner(url):
        """Given a url, return True if the image meets size requirements.

        :param str url: the url of the image to check
        :return: True if the image meets size requirements, False otherwise
        :rtype: bool
        """
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
        except (OSError, IOError) as e:
            logger.error('{}: {}'.format(type(e).__name__, e))
            logger.error('Image URL = {}'.format(url))
            logger.debug('In check_size')
            return False

        # Here's where we use the right logic.
        w, h = img.size
        logger.debug('Image size is {}x{}'.format(w, h))
        return op(w >= min_width, h >= min_height)

    # Return the custom function to the caller.
    return check_size_inner


def is_good_image(img_url):
    """Given an URL, determine if the url points to a file of type jpg or png,
    is greater than a desired size, and does not point to a gallery
    
    :param str img_url: url to determine if points to valid image
    :return: True if valid image, False otherwise
    :rtype: bool
    """

    logger.debug('Check if URL is good image: {}'.format(img_url))
    return 'gallery' not in img_url and \
           ('.jpg' in img_url[-5:] or '.png' in img_url[-5:]) and \
           check_size(img_url)


check_size = create_check_size(min_height, min_width, logic)


def main():
    logger.info('Script Start')

    start_time = 0

    while True:  # Repeat forever.  Break with CTRL-C (on most systems)
        if time.time() - start_time > list_refresh_rate:
            sfw_porn_list = get_new_list(image_subs)
            shower_thought_list = get_new_list(text_subs)
            start_time = time.time()

        img_url = ''
        while True:  # Repeat until we get a valid image in the proper size
            # TODO: fix_url() rather than just imgur
            img_post = random.choice(sfw_porn_list)
            img_url = fix_imgur(img_post.url)
            if is_good_image(img_url):
                logger.debug('Image is from: {}'.format(img_post.url))
                # want to get the subreddit a submission is from
                break

        witty_text = random.choice(shower_thought_list).title
        # They're supposed to all be in the title

        txt_len = len(witty_text)

        if txt_len > 146:
            middle = int(txt_len / 2)
            split = witty_text[:middle].rfind(' ')
            witty_text = witty_text[:split] + '<br>' + witty_text[split:]

        with open(os.path.join(template_path, 'template.html'), 'r') as f:
            template = string.Template(f.read())

        with open(os.path.join(display_path, 'ep_st.html'), 'w') as f:
            f.write(template.substitute(img=img_url, text=witty_text))

        time.sleep(60)


if __name__ == '__main__':
    main()
