from rest_framework import routers
from .api import AnuncioViewSet, CategoriaViewSet

router = routers.DefaultRouter()

router.register(prefix='anuncio', viewset=AnuncioViewSet)
router.register(prefix='categoria', viewset=CategoriaViewSet)


urlpatterns = router.urls