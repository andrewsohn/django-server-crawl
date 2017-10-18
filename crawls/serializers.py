from rest_framework import serializers
from crawls.models import Crawl


class CrawlSerializer(serializers.Serializer):
    number = serializers.IntegerField(default=1000)
    
    sns_kind = serializers.ChoiceField(choices = (
        ('in','instagram'),
        ('in', 'facebook'), 
    ), default='in')

    crawl_type = serializers.ChoiceField(choices = (
        ('all','all'),
        ('tags', 'tags'),
    ), default='all')
    env = serializers.ChoiceField(choices = (
        ('pro','pro'),
        ('dev', 'dev'),
        ('test', 'test'),
    ), default='pro')
    random = serializers.BooleanField(default=False)
    query = serializers.CharField(max_length=100, allow_blank=True)

    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        return Crawl.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        instance.number = validated_data.get('number', instance.number)
        instance.sns_kind = validated_data.get('sns_kind', instance.sns_kind)
        instance.crawl_type = validated_data.get('crawl_type', instance.crawl_type)
        instance.env = validated_data.get('env', instance.env)
        instance.random = validated_data.get('random', instance.random)
        instance.query = validated_data.get('query', instance.query)
        instance.save()
        return instance