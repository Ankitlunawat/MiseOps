from django.urls import path
from operations import api
urlpatterns = [path('api/orders/', api.orders), path('api/orders/<int:pk>/transition/', api.transition), path('api/export/', api.export)]
