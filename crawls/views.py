from django.conf import settings
from rest_framework import status

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework.parsers import JSONParser
import datetime
import json
import csv
import os
from subprocess import call

from crawls.models import Crawl
from crawls.serializers import CrawlSerializer

def csv_len(fname):
    with open(fname) as f:
        csvreader = csv.reader(f)

        row_count = sum(1 for row in csvreader)

    return row_count

class CrawlView(APIView):
	parser_classes = (JSONParser,)
	authentication_classes = (SessionAuthentication, BasicAuthentication)
	permission_classes = (IsAuthenticated,)

	def get(self, request, format=None):
		# print(request.user)

		crawls = Crawl.objects.all()
		serializer = CrawlSerializer(crawls, many=True)
		return Response(serializer.data)

class CrawlSaveView(APIView):
	parser_classes = (JSONParser,)
	authentication_classes = (SessionAuthentication, BasicAuthentication)
	permission_classes = (IsAuthenticated,)

	def get(self, request, format=None):

		serializer = CrawlSerializer(data=request.query_params)

		if serializer.is_valid():

			# 크롤링 실행
			data = serializer.validated_data

			now = datetime.datetime.now()
			# Setting
			setting = settings.CRAWL_SETTING
			csv_dir_prefix = '{}data'.format(settings.CRAWL_PROJ_PATH)
			setting_path = '{}settings.json'.format(settings.CRAWL_PROJ_PATH)
			authentication = '{}auth.json'.format(settings.CRAWL_PROJ_PATH)

			GO_CRAWL_PATH = settings.GO_CRAWL_FB_PATH if data.get('sns_kind') == 'fb' else settings.GO_CRAWL_IN_PATH

			DB_CURRENT_CNT = 0

			loop_cnt = int(data.get('number') / 500)

			# img directory check
			img_dir_path = os.path.join(settings.CRAWL_PROJ_PATH, 'img')
			if not os.path.exists(img_dir_path):
				os.makedirs(img_dir_path)

			# !! CHANGE FROM DB CONNECTION TO FILE SYSTEM !!
			DB_CNT = 0
			csv_filename = "{}-explore-{}".format(data.get('sns_kind'), now.strftime("%Y-%m-%d"))
			csv_file_loc = os.path.join(csv_dir_prefix, "{}.csv".format(csv_filename))

			if os.path.exists(csv_file_loc):
				DB_CNT = csv_len(csv_file_loc)
			else:
				with open(csv_file_loc, 'w') as file:
					file.writelines("id,img,text,has_tag,write_date,reg_date\n")

			DB_TOBE_CNT = DB_CNT + data.get('number')

			while DB_TOBE_CNT > DB_CURRENT_CNT:

				cmd_arr = [settings.GO_CRAWL_CMD, GO_CRAWL_PATH,
						   '-d=' + csv_file_loc,
						   '-t=' + data.get('crawl_type'),
						   '-n=' + str(500),
						   '-a=' + authentication,
						   '-s=' + setting_path,
						   '-e=' + data.get('env')]

				if data.get('query') != "":
					cmd_arr.append('-q={}'.format(data.get('query')))
				elif data.get('random'):
					cmd_arr.append('-r')

				cmd_arr.append('-l')

				print(cmd_arr)
				# subprocess.call(cmd_arr)
				# try:
				call(cmd_arr)
				# except TimeoutExpired as e:
				# 	continue
				# finally:
				# DB_CURRENT_CNT = collection.find({}).count()
				DB_CURRENT_CNT = csv_len(csv_file_loc)

			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CrawlMonitorView(APIView):
	parser_classes = (JSONParser,)
	authentication_classes = (SessionAuthentication, BasicAuthentication)
	permission_classes = (IsAuthenticated,)

	def get(self, request, format=None):

		data = request.query_params

		now = datetime.datetime.now()
		nowDate = now.strftime("%Y%m%d")


		filename = 'logs/log-' + data.get('env') + '.' + nowDate + '.log'
		filename = os.path.join(settings.DIR_PREFIX, filename)

		lines = []
		startNum = 0

		if not data.get('startNum'):

			with open(filename) as fp:
				for i, line in enumerate(fp):
					lines.append({'num':i,'text':line})
		else:
			startNum = int(data.get('startNum'))

			with open(filename) as fp:
				for i, line in enumerate(fp):
					if i > startNum:
						lines.append({'num': i, 'text': line})

		endNum = len(lines) + startNum

		return Response({'log':{
			'startNum':startNum,
			'endNum':endNum,
			'lines':lines
		}}, status=status.HTTP_200_OK)

class CrawlCSVDataView(APIView):
	parser_classes = (JSONParser,)

	def get(self, request, format=None):

		data = request.query_params

		now = datetime.datetime.now()

		csv_dir_prefix = '{}data'.format(settings.CRAWL_PROJ_PATH)
		csv_filename = "{}-explore-{}".format(data.get('sns_kind'), now.strftime("%Y-%m-%d"))
		csv_file_loc = os.path.join(csv_dir_prefix, "{}.csv".format(csv_filename))


		lines = []
		startNum = 0

		if not data.get('startNum'):

			with open(csv_file_loc) as fp:
				for i, line in enumerate(fp):
					lines.append({'num': i, 'text': line})
		else:
			startNum = int(data.get('startNum'))

			with open(csv_file_loc) as fp:
				for i, line in enumerate(fp):
					if i > startNum:
						lines.append({'num': i, 'text': line})

		endNum = len(lines) + startNum

		return Response({'csv': {
			'startNum': startNum,
			'endNum': endNum,
			'lines': lines
		}}, status=status.HTTP_200_OK)
		# return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# def crawl_list(request, format=None):
# 	"""
# 	List all code snippets, or create a new snippet.
# 	"""
# 	# if request.method == 'GET':
# 	# 	crawls = Crawl.objects.all()
# 	# 	serializer = CrawlSerializer(crawls, many=True)
# 	# 	return Response(serializer.data)
#     #
# 	# elif request.method == 'POST':
# 	# crawls = Crawl.objects.all()
# 	# serializer = CrawlSerializer(crawls, many=True)
# 	# print()
# 	# print(JSONParser().parse(request))
# 	# data = JSONParser().parse(request)
# 	# serializer = CrawlSerializer(data=request.data)
# 	# if serializer.is_valid():
# 	# 	serializer.save()
# 	# 	return JsonResponse(serializer.data, status=201)
# 	# return JsonResponse(serializer.errors, status=400)
# 	return Response({'test':request}, status=status.HTTP_201_CREATED)
# 	# serializer = CrawlSerializer(data=request)
# 	# print(data)
# 	# serializer = CrawlSerializer(data=request)
# 	# print(serializer)
# 	# return Response(serializer.data)
#
#
# 	# if serializer.is_valid():
# 	#     serializer.save()
# 	#     return Response(serializer.data, status=status.HTTP_201_CREATED)
# 	# return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET', 'PUT', 'DELETE'])
# def crawl_detail(request, pk):
# 	"""
# 	Retrieve, update or delete a code snippet.
# 	"""
# 	try:
# 		crawl = Crawl.objects.get(pk=pk)
# 	except Crawl.DoesNotExist:
# 		return Response(status=status.HTTP_404_NOT_FOUND)
#
# 	if request.method == 'GET':
# 		serializer = CrawlSerializer(crawl)
# 		return Response(serializer.data)
#
# 	elif request.method == 'PUT':
# 		serializer = CrawlSerializer(crawl, data=request.data)
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# 	elif request.method == 'DELETE':
# 		crawl.delete()
# 		return Response(status=status.HTTP_204_NO_CONTENT)