from rest_framework import serializers
from apps.anuncio.models import Anuncio, Categoria, OfertaAnuncio
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

class CategoriaSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Categoria
        fields= [
            'id',
            'nombre',
            'activa'
        ]

class OfertaAnuncioSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfertaAnuncio
        fields = ['anuncio', 'precio_oferta', 'usuario', 'es_ganador', 'fecha_oferta']
        read_only_fields = ['es_ganador', 'fecha_oferta', 'usuario']

    def validate(self,data):
        try:
            usuario = self.context['request'].user
            instance = OfertaAnuncio(usuario=usuario, **data)
            instance.clean()
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)
        return data
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['anuncio'] = {
            'id' : instance.anuncio.id,
            'titulo': instance.anuncio.titulo,
            'precio_inicial' : instance.anuncio.precio_inicial,
            'fecha_fin': instance.anuncio.fecha_fin,
            'publicado_por': instance.anuncio.publicado_por.username
        }

        representation['usuario'] = {
            'id': instance.usuario.id,
            'username': instance.usuario.username
        }

        return representation

class AnuncioSerializer(serializers.ModelSerializer):
    
    # Manejamos las categorías por su id, pero queremos devolver el objeto completo en la respuesta. Por eso, usamos PrimaryKeyRelatedField 
    # para recibir solo los ids de las categorías, y luego modificamos la representación en to_representation.
    categorias = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), 
        many=True, 
        required=False
    )
    
    class Meta:
        model= Anuncio
        fields = [
            'id', 'titulo', 'descripcion', 'precio_inicial', 'imagen',
            'fecha_inicio', 'fecha_fin', 'activo', 'categorias',
            'publicado_por', 'oferta_ganadora'
        ]
        read_only_fields = ['publicado_por', 'oferta_ganadora']


    # ----- VALIDACIONES PERSONALIZADAS ----- #
    def validate_precio_inicial(self, data):
        request = self.context.get('request') #permite tener contexto de la view en el serializador, si no existe devuelve None
        if request.version == '2':
            if data < 50:
                raise serializers.ValidationError("El precio inicial debe ser mayor o igual a $50")
        elif data <= 0:
            raise serializers.ValidationError("El precio inicial debe ser mayor a $0")

        return data
    
    def validate_fecha_inicio(self, data):
        current_date = timezone.localtime(timezone.now())

        if data < current_date:
            raise serializers.ValidationError(f"La fecha ingresada debe ser superior que la actual - Fecha Actual {current_date}")
        return data
    
    def validate(self, data):
        if data['fecha_fin'] < data['fecha_inicio']:
            raise serializers.ValidationError("La fecha de fin debe ser superior a la fecha inicio")
        return data
    
    
    # ----- REPRESENTACIÓN ANUNCIOS ----- #
    # Usamos to_representation para modificar la respuesta. En este caso, queremos devolver el objeto completo de las categorías, no solo su id.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['categorias'] = CategoriaSerializer(instance.categorias.all(), many=True).data
        return representation