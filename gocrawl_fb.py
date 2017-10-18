from __future__ import division

import argparse
import codecs
from collections import defaultdict
import json
import os
import re
import sys
import asyncio
import time
import random

try:
	from urlparse import urljoin
	from urllib import urlretrieve
except ImportError:
	from urllib.parse import urljoin, quote
	from urllib.request import urlretrieve

import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pymongo
import logging
from logging import FileHandler
from datetime import datetime

from envprint import EnvPrint
from loadbuffererror import LoadBufferError
from timeout import timeout

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._1cr2e._epyes"
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"
FIREFOX_FIRST_POST_PATH = "//div[contains(@class, '_8mlbc _vbtk2 _t5r8b')]"
TIME_TO_CAPTION_PATH = "../../../div/ul/li/span"

# FOLLOWERS/FOLLOWING RELATED
CSS_EXPLORE = "a[href='/explore/']"
CSS_LOGIN = "a[href='/accounts/login/']"
CSS_FOLLOWERS = "a[href='/{}/followers/']"
CSS_FOLLOWING = "a[href='/{}/following/']"
FOLLOWER_PATH = "//div[contains(text(), 'Followers')]"
FOLLOWING_PATH = "//div[contains(text(), 'Following')]"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"

POST_REMOVE = "arguments[0].parentNode.removeChild(arguments[0]);"

now = datetime.now()

class FacebookCrawler(object):
	"""
		Crawler class
	"""
	def __init__(self, headless=True, setting_path='settings.json'):
		# Setting 
		with open(setting_path) as data_file:
			self.setting = json.load(data_file)

		if headless:
			EnvPrint.log_info("headless mode on")
			self._driver = webdriver.PhantomJS(self.setting['PHANTOMJS_PATH'])
			self._driver.set_window_size(1120, 550)
		else:
			self._driver = webdriver.Firefox()

		self._driver.implicitly_wait(10)
		self.data = defaultdict(list)
		
		# DB connection
		connection = pymongo.MongoClient(self.setting['DB_HOST'], self.setting['DB_PORT'])

		db_name = self.setting['DB_NAME']
		self.db = connection[db_name]
		
		collectionName = "fb-explore-{}-Collection".format(now.strftime("%Y-%m-%d"))
		self.collection = self.db[collectionName]

	def crawl(self, dir_prefix, query, crawl_type, number, authentication, is_random):
		EnvPrint.log_info("crawl_type: {}, number: {}, authentication: {}, is_random: {}"
			.format(crawl_type, number, authentication, is_random))
		
		self.crawl_type = crawl_type
		self.is_random = is_random

		if self.crawl_type == "tags":

			if is_random:
				self.query = random.choice(self.setting["HASHTAGS"])
			else:
				self.query = query

			self.crawl_type = crawl_type
			self.accountIdx = 0
			self.totalNum = number
			self.refresh_idx = 0
			self.login(authentication)
			self.browse_target_page()
			try:
				self.scrape_tags(number)
			except Exception:
				EnvPrint.log_info("Quitting driver...")
				self.quit()
		else:
			self.accountIdx = 0
			self.totalNum = number
			self.refresh_idx = 0
			self.login(authentication)

			try:
				self.scrape_tags(number)
			except Exception:
				EnvPrint.log_info("Quitting driver...")
				self.quit()
			
		# Quit driver
		EnvPrint.log_info("Quitting driver...")
		self.quit()

	def login(self, authentication=None):
		"""
			authentication: path to authentication json file
		"""
		# self._driver.get(urljoin(self.setting['FACEBOOK_DOMAIN'], "?sk=h_chr"))
		self._driver.get(self.setting['FACEBOOK_DOMAIN'])
		
		if authentication:
			EnvPrint.log_info("Username and password loaded from {}".format(authentication))
			# print("Username and password loaded from {}".format(authentication))
			with open(authentication, 'r') as fin:
				self.auth_dict = json.loads(fin.read())

			# Input username
			try:
				username_input = WebDriverWait(self._driver, 5).until(
					EC.presence_of_element_located((By.NAME, 'email'))
				)
				username_input.send_keys(self.auth_dict["FACEBOOK"][self.accountIdx]['username'])
			except Exception:
				self._driver.save_screenshot('img/{}'.format('screenshot_login_01.png'))

			# Input password
			try:
				password_input = WebDriverWait(self._driver, 5).until(
					EC.presence_of_element_located((By.NAME, 'pass'))
				)
				password_input.send_keys(self.auth_dict["FACEBOOK"][self.accountIdx]['password'])
	
				# Submit
				password_input.submit()
			except Exception:
				self._driver.save_screenshot('img/{}'.format('screenshot_login_02.png'))

		else:
			EnvPrint.log_info("Type your username and password by hand to login!")
			EnvPrint.log_info("You have a minute to do so!")

		# WebDriverWait(self._driver, 60).until(
		# 	EC.presence_of_element_located((By.CSS_SELECTOR, CSS_EXPLORE))
		# )

	def cleanhtml(self, raw_html):
		cleanr = re.compile('<.*?>')
		cleantext = re.sub(cleanr, '', raw_html)
		return cleantext

	def deletePost(self, div):
		self._driver.execute_script(POST_REMOVE, div)

	def quit(self):
		"""
			Exit Method
		"""
		self._driver.quit()

	def browse_target_page(self):
		# Browse Hashtags
		if hasattr(self, 'query'):
			# if self.is_random:
			# 	self.query = self.query.strip('#')

			query = quote(self.query.encode("utf-8"))

			# https://www.facebook.com/search/str/%23%ED%85%8C%EC%8A%A4%ED%8A%B8/stories-keyword/stories-public
			
			relative_url = urljoin('search/str/', query, '/stories-keyword/stories-public')
			
		else:  # Browse user page
			relative_url = "?sk=h_chr"

		target_url = urljoin(self.setting['FACEBOOK_DOMAIN'], relative_url)

		self._driver.get(target_url)

	@timeout(300)
	def scrape_tags(self, number):
		"""
			scrape_tags method : scraping Instagram image URL & tags
		"""
		post_num = 0

		while post_num < number:

			try:
				self._driver.execute_script(SCROLL_DOWN)
				time.sleep(0.2)
				self._driver.execute_script(SCROLL_UP)
				time.sleep(0.2)

				main_post = self._driver.find_elements_by_xpath("//div[contains(@class, '_4ikz')]")
				org_post = main_post[0]
				post = main_post[0]
				# post = main_post[post_num]
				
				while len(post.find_elements_by_xpath(".//div[contains(@class, '_5pcr') and contains(@class,'fbUserStory')]")):
					post = post.find_elements_by_xpath(".//div[contains(@class, '_5pcr') and contains(@class,'fbUserStory')]")[0]

				see_more_link = post.find_elements_by_xpath(".//a[contains(@class, 'see_more_link')]")

				id = ""
				post_type = ""
				post_id = ""

				if see_more_link :
					link_data = see_more_link[0].get_attribute("href")
					if link_data != "#":
						link_data = link_data.split('?')[0]
						link_data = link_data.replace("https://www.facebook.com/","")
						link_data = link_data.split('/')
						id = link_data[0]
						post_type = link_data[1]
						post_id = link_data[2]

				write_utime_ele = post.find_elements_by_xpath(".//abbr[contains(@class, '_5ptz') and contains(@class, 'timestamp')]")
				write_date = ""
				write_utime = ""

				if write_utime_ele:
					write_utime = write_utime_ele[0].get_attribute("data-utime")
					write_utime = int(write_utime)
					write_date = datetime.utcfromtimestamp(write_utime).isoformat()
					time_atag_href = write_utime_ele[0].find_elements_by_xpath("..")[0].get_attribute("href")
					link_data = time_atag_href.replace("https://www.facebook.com/","")
					# link_data = time_atag_href[1:].split('/')
					link_data = link_data.split('/')
					if(link_data[0] == "groups"):
						id = link_data[1]
						post_type = link_data[0]
						post_id = link_data[2]+'/'+link_data[3]
					else:
						id = link_data[0]
						post_type = link_data[1]
						post_id = link_data[2]
					
				
				text = post.find_elements_by_xpath(".//div[contains(@class, '_5pbx') and contains(@class, 'userContent')]")
				if text:
					text = text[0].get_attribute("innerHTML")
					cleanr = re.compile('<.*?>')
					text = re.sub(cleanr, '', text)
				else:
					text = ""

				img_src_arr = post.find_elements_by_xpath(".//div[contains(@class, '_1dwg') and contains(@class, '_1w_m')]//div[contains(@class, '_3x-2')]//img[@src]")
				img_src = ""

				if img_src_arr:
					img_src = img_src_arr[0].get_attribute("src")

				if self.collection.find({
					"id":id, 
					"post_type":post_type,
					"post_id":post_id,
					"write_utime":write_utime
				}).count() == 0:

					reg_date = datetime.now()
					
					self.collection.insert({"id":id
						,"post_type":post_type
						,"post_id":post_id
						,"img":img_src
						,"text":text
						,"reg_date":reg_date
						,"write_utime":write_utime
					,"write_date":write_date})

					text_enc = text.encode('utf-8')

					EnvPrint.log_info("current post count : {} ---------------------------------".format(post_num))

					EnvPrint.log_info({"id":id
						,"post_type":post_type
						,"post_id":post_id
						,"img":img_src
						,"text":text_enc
						,"reg_date":reg_date
						,"write_utime":write_utime
					,"write_date":write_date})

					post_num = post_num + 1
				
				self.deletePost(org_post)

			except Exception:
				self._driver.save_screenshot('img/{}'.format('screenshot_post_error.png'))

	def nextAuth(self):
		self.accountIdx = 0 if len(self.auth_dict["FACEBOOK"])-1 == self.accountIdx else self.accountIdx+1

	def logoutAndLogin(self):
		self._driver.get(urljoin(self.setting['FACEBOOK_DOMAIN'], "accounts/logout"))

		self._driver.get(urljoin(self.setting['FACEBOOK_DOMAIN'], "accounts/login/"))

		EnvPrint.log_info("Since Instagram provides 5000 post views per Hour, relogin with annother username and password loaded from {}".format(authentication))
		
		# Input username
		try:
			username_input = WebDriverWait(self._driver, 5).until(
				EC.presence_of_element_located((By.NAME, 'email'))
			)
			username_input.send_keys(self.auth_dict["FACEBOOK"][self.accountIdx]['username'])

		except Exception:
			self._driver.save_screenshot('img/{}'.format('screenshot_relogin_01.png'))

		# Input password
		try:
			password_input = WebDriverWait(self._driver, 5).until(
				EC.presence_of_element_located((By.NAME, 'pass'))
			)
			password_input.send_keys(self.auth_dict["FACEBOOK"][self.accountIdx]['password'])
			# Submit
			password_input.submit()
			
		except Exception:
			self._driver.save_screenshot('img/{}'.format('screenshot_relogin_02.png'))
		
		WebDriverWait(self._driver, 60).until(
			EC.presence_of_element_located((By.CSS_SELECTOR, CSS_EXPLORE))
		)

	def scrape_photo_links(self, number, is_hashtag=False):
		EnvPrint.log_info("Scraping photo links...")
		encased_photo_links = re.finditer(r'src="([https]+:...[\/\w \.-]*..[\/\w \.-]*'
								r'..[\/\w \.-]*..[\/\w \.-].jpg)', self._driver.page_source)
		
		photo_links = [m.group(1) for m in encased_photo_links]
		EnvPrint.log_info(photo_links,"pprint")
		# print("Number of photo_links: {}".format(len(photo_links)))

		# begin = 0 if is_hashtag else 1

		# self.data['photo_links'] = photo_links[begin:number + begin]

	def download_and_save(self, dir_prefix, query, crawl_type):
		# Check if is hashtag
		dir_name = query.lstrip(
			'#') + '.hashtag' if query.startswith('#') else query

		dir_path = os.path.join(dir_prefix, dir_name)
		if not os.path.exists(dir_path):
			os.makedirs(dir_path)

		EnvPrint.log_info("Saving to directory: {}".format(dir_path))

		# Save Photos
		for idx, photo_link in enumerate(self.data['photo_links'], 0):
			sys.stdout.write("\033[F")
			EnvPrint.log_info("Downloading {} images to ".format(idx + 1))
			# Filename
			_, ext = os.path.splitext(photo_link)
			filename = str(idx) + ext
			filepath = os.path.join(dir_path, filename)
			# Send image request
			urlretrieve(photo_link, filepath)

		# Save Captions
		for idx, caption in enumerate(self.data['captions'], 0):

			filename = str(idx) + '.txt'
			filepath = os.path.join(dir_path, filename)

			with codecs.open(filepath, 'w', encoding='utf-8') as fout:
				fout.write(caption + '\n')

		# Save followers/following
		filename = crawl_type + '.txt'
		filepath = os.path.join(dir_path, filename)
		if len(self.data[crawl_type]):
			with codecs.open(filepath, 'w', encoding='utf-8') as fout:
				for fol in self.data[crawl_type]:
					fout.write(fol + '\n')

def main():
	#   Arguments  #
	parser = argparse.ArgumentParser(description='Pengtai Instagram Crawler')
	parser.add_argument('-d', '--dir_prefix', type=str,
		default='./data/', help='directory to save results')
	parser.add_argument('-q', '--query', type=str, 
		help="target to crawl, add '#' for hashtags")
	parser.add_argument('-t', '--crawl_type', type=str,
		default='all', help="Options: 'all' | 'tags' | 'photos' | 'following'")
	parser.add_argument('-n', '--number', type=int, default=0,
		help='Number of posts to download: integer')
	parser.add_argument('-l', '--headless', action='store_true',
		help='If set, will use PhantomJS driver to run script as headless')
	parser.add_argument('-a', '--authentication', type=str, default='auth.json',
		help='path to authentication json file')
	parser.add_argument('-s', '--setting', type=str, default='settings.json',
		help='path to setting json file')
	parser.add_argument('-e', '--env', type=str, default='pro',
		help="environment options: 'pro' | 'dev' | 'test'")
	parser.add_argument('-r', '--random', action='store_true',
		help='enables tags mode with random hashtags @ setting.json')

	args = parser.parse_args()
	#  End Argparse #

	nowDate = now.strftime("%Y%m%d")
	filename = './logs/log-'+args.env+'.'+nowDate+'.log'
	FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

	if args.env == "pro":
		logging.basicConfig(filename=filename, level=logging.INFO, format=FORMAT)

	elif args.env == "dev":
		logging.basicConfig(filename=filename,level=logging.DEBUG)
		root = logging.getLogger()
		ch = logging.StreamHandler(sys.stdout)
		ch.setLevel(logging.DEBUG)
		formatter = logging.Formatter(FORMAT)
		ch.setFormatter(formatter)
		root.addHandler(ch)

	EnvPrint.env = args.env

	EnvPrint.log_info("=========================================")
	EnvPrint.log_info(args)

	crawler = FacebookCrawler(headless=args.headless, setting_path = args.setting)
	crawler.crawl(dir_prefix=args.dir_prefix,
		query=args.query,
		crawl_type=args.crawl_type,
		number=args.number,
		authentication=args.authentication,
		is_random=args.random)
	

if __name__ == "__main__":
	main()