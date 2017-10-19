from django.contrib.auth import views as auth_views
from django.conf.urls import url, include
from rest_framework import routers
from django.contrib import admin
admin.autodiscover()
from app import views
from crawls import views as cviews
from rest_framework.urlpatterns import format_suffix_patterns

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
	url(r'^crawl/$', cviews.CrawlView.as_view()),
    url(r'^crawl/save/$', cviews.CrawlSaveView.as_view()),
    url(r'^crawl/monitor/log/$', cviews.CrawlMonitorView.as_view()),
    url(r'^crawl/monitor/csvdata/$', cviews.CrawlCSVDataView.as_view()),
    # url(r'^crawl/(?P<pk>[0-9]+)$', cviews.crawl_detail),
]

urlpatterns = format_suffix_patterns(urlpatterns)

urlpatterns.extend([
	url(r'^$', views.MainView.as_view(), name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^logout$', auth_views.logout, {'next_page' : '/admin/'}, name='logout'),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
])