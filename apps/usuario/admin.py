from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    model = Usuario
    
    # Esto agrega los campos personalizados a la pantalla de "Editar"
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('documento_identidad', 'domicilio')}),
    )
    
    # Esto agrega los campos personalizados a la pantalla de "Agregar" (Lo que te estaba fallando)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {'fields': ('documento_identidad', 'domicilio')}),
    )

# Registramos el modelo con nuestra clase personalizada
admin.site.register(Usuario, UsuarioAdmin)