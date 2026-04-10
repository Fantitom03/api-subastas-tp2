from rest_framework import serializers
from apps.anuncio.models import Anuncio, Categoria
from apps.usuario.models import Usuario

class CategoriaSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Categoria
        fields= [
            'id',
            'nombre',
            'activa'
        ]



# Heredamos de Serializer (no ModelSerializer). 
# Solo definimos los campos que esperamos recibir. Es decir, no hay validación de DB, ni de duplicados, ni nada. Solo validación de tipos y formatos.
class CategoriaAnidadaSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    nombre = serializers.CharField(max_length=100)
    activa = serializers.BooleanField(default=True, required=False)



class AnuncioSerializer(serializers.ModelSerializer):
    # Usamos el serializador "puro"
    categorias = CategoriaAnidadaSerializer(many=True, required=False)
    
    class Meta:
        model= Anuncio
        fields = [
            'id', 'titulo', 'descripcion', 'precio_inicial', 'imagen',
            'fecha_inicio', 'fecha_fin', 'activo', 'categorias',
            'publicado_por', 'oferta_ganadora'
        ]
        read_only_fields = ['publicado_por', 'oferta_ganadora']


    def create(self, validated_data):
        categorias_data = validated_data.pop('categorias', [])
        anuncio = Anuncio.objects.create(**validated_data)
        
        for categoria_data in categorias_data:
            nombre_categoria = categoria_data.get('nombre')
            if nombre_categoria:
                # Como la validación de duplicados no frenó la petición, puedo ejecutar esto
                categoria, _ = Categoria.objects.get_or_create(nombre=nombre_categoria)
                anuncio.categorias.add(categoria)
                
        return anuncio

    def update(self, instance, validated_data):
        categorias_data = validated_data.pop('categorias', []) 

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        nuevas_categorias = []
        for categoria_data in categorias_data:
            nombre_categoria = categoria_data.get('nombre')
            if nombre_categoria:
                categoria, _ = Categoria.objects.get_or_create(nombre=nombre_categoria)
                nuevas_categorias.append(categoria)

        instance.categorias.set(nuevas_categorias) 
        return instance
    
class TiempoRestanteSerializer(serializers.Serializer):
    dias = serializers.IntegerField()
    horas = serializers.IntegerField()
    minutos = serializers.IntegerField()
