from rest_framework import serializers
from apps.anuncio.models import Anuncio, Categoria, OfertaAnuncio
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from decimal import Decimal
from dotenv import load_dotenv
import os
import requests

load_dotenv()


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
    precio_usd = serializers.SerializerMethodField()

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
            'uuid', 'titulo', 'descripcion', 'precio_inicial', 'imagen',
            'fecha_inicio', 'fecha_fin', 'activo', 'categorias',
            'publicado_por', 'oferta_ganadora', 'precio_usd'
        ]
        read_only_fields = ['publicado_por', 'oferta_ganadora', 'uuid', 'precio_usd']


    # ----- VALIDACIONES PERSONALIZADAS ----- #
    def validate_precio_inicial(self, data):
        request = self.context.get('request') #permite tener contexto de la view en el serializador, si no existe devuelve None
        #No conviene hacer los controles de las versiones en el serializador. Es mejor hacerlos en la vista, para mantener el serializador lo más limpio posible. Sin embargo, lo hacemos aquí solo a modo de ejemplo.
        #Si necesitamos hacer un control diferente lo mejor sería hacer otro serializador para esa versión, y así mantener el código más limpio y organizado. De esta forma, cada serializador se encargaría de las validaciones específicas de su versión, evitando la necesidad de controles condicionales dentro de un mismo método de validación.
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
    
    #Tenemos que utilizarlo para validaciones de campos relacionados, como en este caso, donde queremos comparar fecha_inicio con fecha_fin. Si intentamos hacer esta validación en validate_fecha_fin, no podremos acceder a fecha_inicio porque aún no se ha validado.
    def validate(self, data):
        # Tomamos los valores de 'data' (si vienen en el PATCH/POST) o de 'self.instance' (si ya existen en la BD y no se están modificando)
        fecha_inicio = data.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_fin = data.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        
        # Solo validamos si ambas fechas existen
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise serializers.ValidationError("La fecha de fin debe ser superior a la fecha inicio")
                
        return data
    
    
    # ----- REPRESENTACIÓN ANUNCIOS ----- #
    # Usamos to_representation para modificar la respuesta. En este caso, queremos devolver el objeto completo de las categorías, no solo su id.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['categorias'] = CategoriaSerializer(instance.categorias.all(), many=True).data
        return representation
    

    def obtener_dolar(self):
        key = os.getenv('EXCHANGERATE_API_KEY')
        try:
            response = requests.get(f'https://v6.exchangerate-api.com/v6/{key}/latest/ARS')

            data = response.json()

            return Decimal(str(data["conversion_rates"]["USD"]))
        
        except requests.exceptions.HTTPError as http_err:
            return JsonResponse({"error": "Hubo un problema al consultar el servicio externo."}, status = 502)
        
        except requests.exceptions.ConnectionError as conn_err:
            return JsonResponse({"error": "No se pudo conectar al servicio externo. Inténtelo más tarde"}, status = 502)
        
        except requests.exceptions.Timeout as timeout_err:
            return JsonResponse({"error": "El servicio externo tardó demasiado en responder"}, status = 504)
        
        except requests.exceptions.RequestException as err:
            return JsonResponse({"error": "Ocurró un error inesperado al contactar el serivcio externo"}, status = 500)
    
    def get_precio_usd(self,obj):
        if not hasattr(self, "_usd_rate"):
            self._usd_rate = self.obtener_dolar()

        return round(obj.precio_inicial * self._usd_rate, 2)