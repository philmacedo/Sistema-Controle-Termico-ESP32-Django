"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from philApp import views
from cpcApp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    #path('minha_view/', views.minha_view, name='minha_view'),
    #path('atualizacao_dados/<str:numero_serial>/<str:entrada_analogica>/<str:entrada_digital>/',
    #   views.atualizacao_dados, name='atualizacao_dados'),
    #path('registrar/<str:numero_serial>/<str:temperatura>/', views.registrar, name='registra'),
    #path('media_temperaturas/', views.media_temperaturas),
    path('', views.index, name='index'),
    path('gravar/<str:device_id>/<str:temp>/<int:duty>/<int:relay>/<int:door>/<int:vibra>/',
         views.receber_telemetria, name='receber_telemetria'),
    path('status/<str:device_id>/', views.dados_dashboard, name='dados_dashboard'),
    path('setpoint/<str:device_id>/<str:novo_setpoint>/', views.definir_setpoint, name='definir_setpoint'),
    path('emergencia/<str:device_id>/', views.alternar_emergencia, name='alternar_emergencia'),
]
