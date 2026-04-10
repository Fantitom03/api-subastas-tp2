from rest_framework import routers
from .api import AnuncioViewSet

router = routers.DefaultRouter()

router.register(prefix='anuncio', viewset=AnuncioViewSet)

urlpatterns = router.urls