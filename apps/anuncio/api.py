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
from rest_framework.permissions import IsAuthenticated
from .permissions import IsPropietarioOrReadOnly
from rest_framework import status




class AnuncioViewSet(viewsets.ModelViewSet):
    queryset = Anuncio.objects.all()
    serializer_class = AnuncioSerializer
    # Usar el UUID en la URL en lugar del ID
    lookup_field = 'uuid' 

    # Aplicamos el permiso de DjangoModelPermissions y nuestro nuevo permiso IsPropietarioOrReadOnly
    permission_classes = [IsAuthenticated, IsPropietarioOrReadOnly]


    #----Configuración de filtros, ordenamiento y búsqueda----#
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    # Filtros personalizados
    filterset_class = AnuncioFilter
    ordering_fields = ['precio_inicial', 'fecha_publicacion', 'fecha_inicio']
    # Campos del queryset que se pueden usar para realizar búsquedas de texto
    search_fields = ['titulo', 'descripcion']


    #---- Método para asignar automáticamente el usuario autenticado como el publicador del anuncio----#
    
    def perform_create(self, serializer):
        usuario_a_asignar = self.request.user

        serializer.save(publicado_por=usuario_a_asignar)

    #ENDPOINT PERSONALIZADO: Endpoint para obtener el tiempo restante de un anuncio
    @action(detail=True, methods=['get'])
    def get_remaining_time(self, request, uuid=None):
        anuncio = self.get_object()

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

    # ENDPOINT DE OFERTAS: Endpoint anidado para hacer ofertas
    @action(detail=True, methods=['post', 'get'], permission_classes=[IsAuthenticated])
    def ofertas(self, request, uuid=None):
        anuncio = self.get_object()

        # Si es un GET, devolvemos las ofertas de este anuncio
        if request.method == 'GET':
            ofertas = anuncio.ofertas.all()
            serializer = OfertaAnuncioSerializer(ofertas, many=True)
            return Response(serializer.data)

        # Si es un POST, creamos una nueva oferta
        if request.method == 'POST':
            # Verificamos explícitamente que el anuncio esté activo antes de aceptar ofertas
            if not anuncio.activo:
                return Response(
                    {"detail": "No se pueden realizar ofertas en un anuncio inactivo."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Inyectamos el ID del anuncio en los datos de la petición
            data = request.data.copy()
            data['anuncio'] = anuncio.id

            # Pasamos el request en el contexto para que el serializer sepa quién es el usuario
            serializer = OfertaAnuncioSerializer(data=data, context={'request': request})
            
            if serializer.is_valid():
                # El serializer (gracias aL clean() en el modelo) ya validará automáticamente:
                # 1. Que el usuario no sea el creador.
                # 2. Que el precio sea mayor al inicial y a la última oferta.
                # 3. Que no haya expirado por fecha.
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    
    # Configuración de filtros, ordenamiento y búsqueda
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # El filterset_class nos permite definir un conjunto de filtros personalizados para nuestro modelo
    filterset_class = CategoriaFilter
    # El ordering_fields nos permite definir los campos por los cuales se puede ordenar la consulta.
    ordering_fields = ['nombre']

