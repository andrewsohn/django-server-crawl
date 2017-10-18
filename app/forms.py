from django import forms

from crawls.models import Crawl

class CrawlForm(forms.ModelForm):

    class Meta:
        model = Crawl
        fields = ('sns_kind', 'number', 'crawl_type', 'env', 'random', 'query',)