from rest_framework import permissions

#Permiso personalizado para verificar que el usuario autenticado sea el propietario del anuncio
class IsPropietarioOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        #Metodos de lectura (GET, HEAD, OPTIONS), que son permitidos para cualquier usuario autenticado
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Para métodos de escritura (PUT, PATCH, DELETE), verificamos que el usuario  autenticado sea el mismo que publicó el anuncio.
        return obj.publicado_por == request.user