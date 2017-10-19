from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect
from rest_framework import viewsets, status
from app.serializers import UserSerializer, GroupSerializer
from django.shortcuts import render
from django.views import View
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
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

# def (request):
#     """
#     API endpoint that allows groups to be viewed or edited.
#     """
#
#     return render(request, 'index.html', {'form': form})

class MainView(View):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not request.session.session_key:
            return HttpResponseRedirect('/admin/')
        # print(request.auth)

        form = CrawlForm()
        return render(request, 'index.html', {'form': form})