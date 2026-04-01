from rest_framework import serializers
from .models import Anuncio, Categoria
from apps.usuario.models import Usuario

class CategoriaSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Categoria
        fields= [
            'id',
            'nombre',
            'activa'
        ]
        extra_kwargs = {
            'nombre': {
                'validators': [], 
            }
        }

class AnuncioSerializer(serializers.ModelSerializer):
    categorias = CategoriaSerializer(many=True)
    class Meta:
        model= Anuncio
        fields = [
            'id',
            'titulo',
            'descripcion',
            'precio_inicial',
            'imagen',
            'fecha_inicio',
            'fecha_fin',
            'activo',
            'categorias',
            'publicado_por',
            'oferta_ganadora'
        ]
        read_only_fields = ['publicado_por', 'oferta_ganadora']

    def create(self, validated_data):
        # Sacamos las categorías del diccionario de datos validados
        categorias_data = validated_data.pop('categorias')
        
        # Creamos el Anuncio con el resto de los datos (título, precio, etc.)
        anuncio = Anuncio.objects.create(**validated_data)
        
        # Procesamos cada categoría
        for categoria_data in categorias_data:
            nombre_categoria = categoria_data.get('nombre')
            
            # get_or_create devuelve una tupla: (el_objeto, fue_creado_booleano)
            # Usamos "_" para ignorar el booleano porque solo nos importa el objeto
            if nombre_categoria:
                categoria, _ = Categoria.objects.get_or_create(nombre=nombre_categoria)
                
                # Agregamos la categoría a la relación del Anuncio
                anuncio.categorias.add(categoria)
                
        return anuncio
    
    def update(self, instance, validated_data):
        categorias_data = validated_data.pop('categorias', []) #Se toma solo lo ingresado en categorias

        #Se instancian los demas elementos, como sean nombre, descripcion, etc.
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        #Almacenará las nuevas categorias
        nuevas_categorias = []

        #Recorremos cada categoria ingresada
        for categoria_data in categorias_data:
            categoria_id = categoria_data.get('id') #Se obtiene el id
            nombre_categoria = categoria_data.get('nombre') #Se obtiene el nombre
            if categoria_id: #En caso de que exista ID
                try:
                    categoria = Categoria.objects.get(id=categoria_id) #Obtener el objeto categoria por ID
                except Categoria.DoesNotExist:
                    categoria, _ = Categoria.objects.get_or_create(nombre=nombre_categoria) #Si es un ID invalido, hay que obtener el objeto categoria por nombre
            else:
                categoria, _ = Categoria.objects.get_or_create(nombre=nombre_categoria) #Obtener el objeto categoria por nombre
            
            nuevas_categorias.append(categoria) #Agregamos la "nueva" categoria

        instance.categorias.set(nuevas_categorias) #Las seteamos en la instancia de anuncios

        return instance #retornamos el anuncio
        