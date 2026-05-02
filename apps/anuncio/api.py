from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Anuncio, Categoria, OfertaAnuncio
from apps.usuario.models import Usuario
from .serializers import AnuncioSerializer, CategoriaSerializer, OfertaAnuncioSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .filters import AnuncioFilter, CategoriaFilter

class AnuncioViewSet(viewsets.ModelViewSet):
    queryset = Anuncio.objects.all()
    serializer_class = AnuncioSerializer

    # Configuración de filtros, ordenamiento y búsqueda
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    # El filterset_class nos permite definir un conjunto de filtros personalizados para nuestro modelo
    filterset_class = AnuncioFilter
    # El ordering_fields nos permite definir los campos por los cuales se puede ordenar la consulta.
    ordering_fields = ['precio_inicial', 'fecha_publicacion', 'fecha_inicio']
    # El search_fields nos permite definir los campos por los cuales se puede realizar una búsqueda de texto completo. Admitiendo busquedas parciales e insensibles a mayúsculas.
    search_fields = ['titulo', 'descripcion']

    def perform_create(self, serializer):
        usuario_a_asignar = self.request.user

        serializer.save(publicado_por=usuario_a_asignar)

    @action(detail=True, methods=['get'])
    def get_remaining_time(self, request, pk=None):
        anuncio = get_object_or_404(Anuncio, pk=pk)

        last_date = anuncio.fecha_fin
        current_date = timezone.localtime(timezone.now())
        
        remaining_time = last_date - current_date

        if request.version == '2': 
            return Response(
                {
                    'status': 'Pronto a finalizar' if remaining_time.days < 2 else 'Lejos de finalizar',
                    'message': f'Quedan {remaining_time.days} Dias {remaining_time.seconds // 3600} Horas {(remaining_time.seconds // 60) % 60} Minutos',
                }  
            )

        return Response(
            {
                'dias': remaining_time.days,
                'horas': remaining_time.seconds // 3600,
                'minutos': (remaining_time.seconds // 60) % 60,
            } 
        ) 



class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    
    # Configuración de filtros, ordenamiento y búsqueda
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # El filterset_class nos permite definir un conjunto de filtros personalizados para nuestro modelo
    filterset_class = CategoriaFilter
    # El ordering_fields nos permite definir los campos por los cuales se puede ordenar la consulta.
    ordering_fields = ['nombre']


class OfertaAnuncioViewSet(viewsets.ModelViewSet):
    queryset = OfertaAnuncio.objects.all()
    serializer_class = OfertaAnuncioSerializer

    def perform_create(self, serializer):
        usuario_a_asignar = self.request.user

        serializer.save(usuario=usuario_a_asignar)

