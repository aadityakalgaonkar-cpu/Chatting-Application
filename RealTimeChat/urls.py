"""
URL configuration for RealTimeChat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from RealTimeChat import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('registration/',views.userregistration,name='registration'),
    path('',views.userlogin,name='root'),
    path('login/',views.userlogin,name='login'),
    path('homepage/',views.homepage,name='homepage'),
    path('logout/',views.userlogout,name='logout'),
    path("search-user/", views.search_user, name="search_user"),
    path("chat/<int:conversation_id>/",views.chat,name='chat'),
    path("open-chat/<int:user_id>/",views.open_chat,name="open_chat"),
    
]
