from rest_framework import serializers
from apps.anuncio.models import Anuncio, Categoria
from django.utils import timezone

class CategoriaSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Categoria
        fields= [
            'id',
            'nombre',
            'activa'
        ]



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
        if data['fecha_fin'] < data['fecha_inicio']:
            raise serializers.ValidationError("La fecha de fin debe ser superior a la fecha inicio")
        return data
    
    
    # ----- REPRESENTACIÓN ANUNCIOS ----- #
    # Usamos to_representation para modificar la respuesta. En este caso, queremos devolver el objeto completo de las categorías, no solo su id.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['categorias'] = CategoriaSerializer(instance.categorias.all(), many=True).data
        return representation