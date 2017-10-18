from __future__ import division

import argparse
import codecs
from collections import defaultdict
import json
import csv
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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
# import pymongo
import logging
import datetime

from envprint import EnvPrint
from timeout import timeout

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._1cr2e._epyes"
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"
FIREFOX_FIRST_POST_PATH = "//div[contains(@class, '_8mlbc _vbtk2 _t5r8b')]"
TIME_TO_CAPTION_PATH = "../../../div/ul/li/span"

# FOLLOWERS/FOLLOWING RELATED
CSS_EXPLORE_MAIN = "main._8fi2q._2v79o"
CSS_EXPLORE = "a[href='/explore/']"
CSS_EXPLORE_MAIN_LIST = "article._gupiw"
CSS_LOGIN = "a[href='/accounts/login/']"
CSS_FOLLOWERS = "a[href='/{}/followers/']"
CSS_FOLLOWING = "a[href='/{}/following/']"
FOLLOWER_PATH = "//div[contains(text(), 'Followers')]"
FOLLOWING_PATH = "//div[contains(text(), 'Following')]"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"

POST_REMOVE = "if('undefined' !== typeof arguments && arguments[0] > 0){ \
 var ele = document.getElementsByClassName('_70iju'); \
 var prnt = ele[ele.length-1].parentNode; \
 for(var i=0; i<arguments[0]; i++){ \
 var temp_ele = document.getElementsByClassName('_70iju'); \
 temp_ele[0].parentNode.removeChild(temp_ele[0].parentNode.firstChild); \
 } \
 }"
# POST_REMOVE = "if('undefined' !== typeof arguments && arguments[0] > 0){ \
#  var ele = document.getElementsByClassName('_70iju'); \
#  var prnt = ele[ele.length-1].parentNode; \
#  for(var i=0; i<arguments[0]; i++){ \
#  var temp_ele = document.getElementsByClassName('_70iju'); \
#  console.log(arguments[0], temp_ele);\
#  temp_ele[0].parentNode.removeChild(temp_ele[0].parentNode.firstChild); \
#  } \
#  }"

now = datetime.datetime.now()

class InstagramCrawler(object):
	"""
		Crawler class
	"""
	def __init__(self, headless=True, setting_path='settings.json'):
		# Setting
		with open(setting_path) as data_file:
			self.setting = json.load(data_file)

		if headless:
			EnvPrint.log_info("headless mode on")
			self._driver = webdriver.PhantomJS("{}/node_modules/phantomjs/bin/phantomjs".format(os.path.dirname(os.path.abspath(__file__))))
			self._driver.set_window_size(1120, 550)
		else:
			self._driver = webdriver.Firefox()

		self._driver.implicitly_wait(10)
		self.data = defaultdict(list)

		# DB connection
		# connection = pymongo.MongoClient(self.setting['DB_HOST'], self.setting['DB_PORT'])
		# db_name = self.setting['DB_NAME']
		# self.db = connection[db_name]
		# collectionName = "in-explore-{}-Collection".format(now.strftime("%Y-%m-%d"))
		# self.collection = self.db[collectionName]

	def crawl(self, csv_file_loc, query, crawl_type, number, authentication, is_random):
		EnvPrint.log_info("crawl_type: {}, number: {}, authentication: {}, is_random: {}"
			.format(crawl_type, number, authentication, is_random))

		# !! CHANGE FROM DB CONNECTION TO FILE SYSTEM !!

		self.csv_file_loc = csv_file_loc

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
			self.browse_target_page()
			try:
				self.scrape_tags(number)
			except Exception:
				EnvPrint.log_info("Quitting driver...")
				self.quit()
		# 	EnvPrint.log_info("Unknown crawl type: {}".format(crawl_type))
		# 	self.quit()
		# 	return

		#Quit driver
		EnvPrint.log_info("Quitting driver...")
		self.quit()

	def login(self, authentication=None):
		"""
			authentication: path to authentication json file
		"""
		self._driver.get(urljoin(self.setting['INSTA_DOMAIN'], "accounts/login/"))

		if authentication:
			EnvPrint.log_info("Username and password loaded from {}".format(authentication))
			# print("Username and password loaded from {}".format(authentication))
			with open(authentication, 'r') as fin:
				self.auth_dict = json.loads(fin.read())

			# Input username
			try:
				username_input = WebDriverWait(self._driver, 5).until(
					EC.presence_of_element_located((By.NAME, 'username'))
				)
				username_input.send_keys(self.auth_dict["INSTAGRAM"][self.accountIdx]['username'])
			except Exception:
				self._driver.save_screenshot('img/{}'.format('screenshot_login_01.png'))

			# Input password
			try:
				password_input = WebDriverWait(self._driver, 5).until(
					EC.presence_of_element_located((By.NAME, 'password'))
				)
				password_input.send_keys(self.auth_dict["INSTAGRAM"][self.accountIdx]['password'])

				# Submit
				password_input.submit()
			except Exception:
				self._driver.save_screenshot('img/{}'.format('screenshot_login_02.png'))

		else:
			EnvPrint.log_info("Type your username and password by hand to login!")
			EnvPrint.log_info("You have a minute to do so!")

		WebDriverWait(self._driver, 60).until(
			EC.presence_of_element_located((By.CSS_SELECTOR, CSS_EXPLORE))
		)


	def quit(self):
		"""
			Exit Method
		"""
		self._driver.quit()

	def browse_target_page(self):
		# Browse Hashtags
		if hasattr(self, 'query'):
			if self.is_random:
				self.query = self.query.strip('#')

			query = quote(self.query.encode("utf-8"))

			relative_url = urljoin('explore/tags/', query.strip('#'))

		else:  # Browse user page
			relative_url = "explore"

		target_url = urljoin(self.setting['INSTA_DOMAIN'], relative_url)

		self._driver.get(target_url)

	@timeout(300)
	def scrape_tags(self, number):
		"""
			scrape_tags method : scraping Instagram image URL & tags
		"""
		if self.crawl_type == "tags":
			try:
				# scroll page until reached
				loadmore = WebDriverWait(self._driver, 10).until(
					EC.presence_of_element_located((By.CSS_SELECTOR, CSS_LOAD_MORE))
				)
				loadmore.click()
			except Exception:
				self._driver.save_screenshot('img/{}'.format('screenshot_tags_loadmore.png'))


		async def deletePost(num):
			rowNum = int(num / 3)
			self._driver.execute_script(POST_REMOVE, rowNum)

		async def savePost(new_list):
			ignore_num = 0

			for i in range(0, len(new_list)):

				ahref_arr = new_list[i].find_elements_by_xpath(".//a")[0].get_attribute("href").split('/')
				id = ahref_arr[len(ahref_arr)-2]

				img_src = new_list[i].find_elements_by_xpath(".//img[@class='_2di5p']")[0].get_attribute("src")
				text = new_list[i].find_elements_by_xpath(".//img[@class='_2di5p']")[0].get_attribute("alt")
				reg_date = datetime.datetime.now()
				write_date = None

				try:
					response = requests.head(img_src, timeout=1)
					write_date = response.headers["last-modified"]

				except requests.exceptions.Timeout:
					write_date = ""
				finally:
					if text:
						exist_ids = None
						with open(self.csv_file_loc) as f:
							csvreader = csv.reader(f)
							exist_ids = [row[0] for row in csvreader]

						if id in exist_ids:
							ignore_num = ignore_num + 1
						else:

							with open(self.csv_file_loc, 'a') as file:
								# file.write("{},{},{},{},{},{}\n".format(id, img_src, text, self.query, write_date, reg_date))

								csvwriter = csv.writer(file)
								csvwriter.writerow([id, img_src, text, self.query, write_date, reg_date])

							text_enc = text.encode('utf-8')

							EnvPrint.log_info({"id":id
							,"img":img_src
							,"text":text_enc
							,"has_tag":self.query
							,"write_date":write_date
							,"reg_date":reg_date}, "debug")

				# 			# self.collection.insert({"id":id
				# 			# ,"img":img_src
				# 			# ,"text":text
				# 			# ,"has_tag":self.query
				# 			# ,"write_date":write_date
				# 			# ,"reg_date":reg_date})



			last_post_num_new = len(new_list) - ignore_num

			return last_post_num_new

		async def loop_func(last_post_num, load_idx, loop):
			last_post_num_pre = last_post_num
			load_idx = load_idx

			while last_post_num_pre <= number:
				self._driver.execute_script(SCROLL_DOWN)
				time.sleep(0.2)

				# explore_main_list_new = await get_new_posts()

				try:
					WebDriverWait(self._driver, 3).until(
						EC.presence_of_element_located((By.XPATH, "//div[contains(@class, '_mck9w') and contains(@class,'_gvoze') and contains(@class,'_f2mse')]"))
					)

					explore_main_list_new = self._driver.find_elements_by_xpath("//div[contains(@class, '_mck9w') and contains(@class,'_gvoze') and contains(@class,'_f2mse')]")

					if last_post_num_pre >= len(explore_main_list_new):
						continue

					last_post_num_new = await savePost(explore_main_list_new)

					load_idx=load_idx+1
					cur_post_count = last_post_num_pre+last_post_num_new

					if self.crawl_type == "tags":
						EnvPrint.log_info("current post count : {}, tags : {} ---------------------------------".format(cur_post_count, self.query))
					else:
						EnvPrint.log_info("current post count : {} ---------------------------------".format(cur_post_count))

					EnvPrint.log_info("post crawling done ------------------------------------------", "debug")

					last_post_num_pre = cur_post_count

					# await deletePost(last_post_num_new)
				except Exception:
					self._driver.save_screenshot('img/{}'.format('screenshot_post_error.png'))

					# error_box = self._driver.find_elements_by_xpath("//div[contains(@class, '_fb78b')]")
					# if last_post_num_new == 0:
					# 	self.leftover_num = number - last_post_num
					# 	raise Exception("error")

			loop.stop()

		loop = asyncio.get_event_loop()

		load_idx = 0
		last_post_num = 0

		loop.run_until_complete(loop_func(last_post_num, load_idx, loop))
		loop.run_forever()
		# except Exception as e:
		# 	loop.stop()
		# 	if e == "error":
		# 		self.nextAuth()
		# 		self.logoutAndLogin()
		# 		self.browse_target_page("explore")
		# 		loop.close()
		# 		loop.run_until_complete(loop_func(self.leftover_num, 0, loop))
		# 		loop.run_forever()
		# 		# self.scrape_tags(self.leftover_num)

		# 	print("ok------------------------------")
		# finally:
		loop.close()

	def nextAuth(self):
		self.accountIdx = 0 if len(self.auth_dict["INSTAGRAM"])-1 == self.accountIdx else self.accountIdx+1

	def logoutAndLogin(self):
		self._driver.get(urljoin(self.setting['INSTA_DOMAIN'], "accounts/logout"))

		self._driver.get(urljoin(self.setting['INSTA_DOMAIN'], "accounts/login/"))

		EnvPrint.log_info("Since Instagram provides 5000 post views per Hour, relogin with annother username and password loaded from {}".format(authentication))

		# Input username
		try:
			username_input = WebDriverWait(self._driver, 5).until(
				EC.presence_of_element_located((By.NAME, 'username'))
			)
			username_input.send_keys(self.auth_dict["INSTAGRAM"][self.accountIdx]['username'])

		except Exception:
			self._driver.save_screenshot('img/{}'.format('screenshot_relogin_01.png'))

		# Input password
		try:
			password_input = WebDriverWait(self._driver, 5).until(
				EC.presence_of_element_located((By.NAME, 'password'))
			)
			password_input.send_keys(self.auth_dict["INSTAGRAM"][self.accountIdx]['password'])
			# Submit
			password_input.submit()

		except Exception:
			self._driver.save_screenshot('img/{}'.format('screenshot_relogin_02.png'))

		WebDriverWait(self._driver, 60).until(
			EC.presence_of_element_located((By.CSS_SELECTOR, CSS_EXPLORE))
		)

	# def scroll_to_num_of_posts(self, number):
		# Get total number of posts of page
		# print(self._driver.page_source)
		# num_info = re.search(r'\], "count": \d+',
		# 				self._driver.page_source).group()

		# num_of_posts = int(re.findall(r'\d+', num_info)[0])
		# print("posts: {}, number: {}".format(num_of_posts, number))
		# number = number if number < num_of_posts else num_of_posts

		# # scroll page until reached
		# loadmore = WebDriverWait(self._driver, 10).until(
		# 	EC.presence_of_element_located((By.CSS_SELECTOR, CSS_LOAD_MORE))
		# )
		# loadmore.click()

		# num_to_scroll = int((number - 12) / 12) + 1
		# for _ in range(num_to_scroll):
		# 	self._driver.execute_script(SCROLL_DOWN)
		# 	time.sleep(0.2)
		# 	self._driver.execute_script(SCROLL_UP)
		# 	time.sleep(0.2)

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
	parser.add_argument('-d', '--csv_file_loc', type=str,
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

	crawler = InstagramCrawler(headless=args.headless, setting_path = args.setting)
	crawler.crawl(csv_file_loc=args.csv_file_loc,
		query=args.query,
		crawl_type=args.crawl_type,
		number=args.number,
		authentication=args.authentication,
		is_random=args.random)
	

if __name__ == "__main__":
	main()