from django.db import models
from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles

LEXERS = [item for item in get_all_lexers() if item[1]]
LANGUAGE_CHOICES = sorted([(item[1][0], item[0]) for item in LEXERS])
STYLE_CHOICES = sorted((item, item) for item in get_all_styles())


class Crawl(models.Model):
	number = models.IntegerField(default=1000)
	reg_date = models.DateTimeField(auto_now_add=True)
	sns_kind = models.CharField(max_length=2, choices = (
		('in','instagram'),
		('in', 'facebook'), 
	), default='in')

	crawl_type = models.CharField(max_length=5, choices = (
		('all','all'),
		('tags', 'tags'),
	), default='all')
	env = models.CharField(max_length=5, choices = (
		('pro','pro'),
		('dev', 'dev'),
		('test', 'test'),
	), default='pro')
	random = models.BooleanField(default=False)
	query = models.CharField(max_length=100, null=True, blank=True)

	# created = models.DateTimeField(auto_now_add=True)
	# title = models.CharField(max_length=100, blank=True, default='')
	# code = models.TextField()
	# linenos = models.BooleanField(default=False)
	# language = models.CharField(choices=LANGUAGE_CHOICES, default='python', max_length=100)
	# style = models.CharField(choices=STYLE_CHOICES, default='friendly', max_length=100)

	class Meta:
		ordering = ('reg_date',)