from django.urls import re_path
from gateway.views import proxy_auth, proxy_core

urlpatterns = [
    re_path(r'^api/auth/(?P<path>.*)$', proxy_auth),
    re_path(r'^api/(?P<path>.*)$', proxy_core),
]
