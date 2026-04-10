from rest_framework import viewsets
from .models import Anuncio
from apps.usuario.models import Usuario
from .serializers import AnuncioSerializer, TiempoRestanteSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404

class AnuncioViewSet(viewsets.ModelViewSet):
    queryset = Anuncio.objects.all()
    serializer_class = AnuncioSerializer

    def perform_create(self, serializer):
        usuario_a_asignar = Usuario.objects.first()

        serializer.save(publicado_por=usuario_a_asignar)

    @action(detail=True, methods=['get'])
    def get_remaining_time(self, request, pk=None):
        anuncio = get_object_or_404(self.get_queryset(), pk=pk)

        fecha_fin = anuncio.fecha_fin
        fecha_actual = timezone.now()
        
        if fecha_fin > fecha_actual: 
            tiempo_restante = fecha_fin - fecha_actual

            data = {
                'dias': tiempo_restante.days,
                'horas': tiempo_restante.seconds // 3600,
                'minutos': (tiempo_restante.seconds // 60) % 60,
            }    
        else:
            data = {
                'dias': 0,
                'horas': 0,
                'minutos': 0,
            }  

        serializer = TiempoRestanteSerializer(data)

        return Response(serializer.data)



