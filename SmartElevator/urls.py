from django.urls import path
from .views import *

urlpatterns = [
    path("add_request/",add_request),
    path("move_elevator/", move_elevator),
    path("emergency_on/",emergency_on),
    path("emergency_off/",emergency_off),
]