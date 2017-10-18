from django.contrib.auth.models import User, Group
from rest_framework import viewsets, status
from app.serializers import UserSerializer, GroupSerializer
from django.shortcuts import render
from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .forms import CrawlForm


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

def MainViewSet(request):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    form = CrawlForm()
    return render(request, 'index.html', {'form': form})
