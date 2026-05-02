from rest_framework import routers
from .api import AnuncioViewSet, CategoriaViewSet,OfertaAnuncioViewSet

router = routers.DefaultRouter()

router.register(prefix='anuncio', viewset=AnuncioViewSet)
router.register(prefix='categoria', viewset=CategoriaViewSet)
router.register(prefix='oferta', viewset=OfertaAnuncioViewSet)


urlpatterns = router.urls