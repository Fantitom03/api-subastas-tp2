from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Anuncio(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio_inicial = models.DecimalField(decimal_places=2, max_digits=10)
    imagen = models.FileField(blank=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    categorias = models.ManyToManyField(Categoria, blank=True)
    publicado_por = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE, related_name='anuncios_publicados')
    oferta_ganadora = models.OneToOneField('OfertaAnuncio', on_delete=models.SET_NULL,
                                           related_name='oferta_ganadora', blank=True, null=True)

    class Meta:
        ordering = ('fecha_inicio',)

    def __str__(self):
        return f'{self.titulo} - {"Activo" if self.activo else "Inactivo"} '


class SeguimientoAnuncio(models.Model):
    fecha = models.DateTimeField(auto_now=True)
    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name='seguimientos')
    usuario = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE, related_name='seguimientos_anuncios')

    def __str__(self):
        return f'Anuncio: {self.anuncio.titulo} - Usuario: {self.usuario}'


class OfertaAnuncio(models.Model):
    anuncio = models.ForeignKey('Anuncio', on_delete=models.CASCADE, related_name='ofertas')
    fecha_oferta = models.DateTimeField(auto_now_add=True)
    precio_oferta = models.DecimalField(decimal_places=2, max_digits=10)
    es_ganador = models.BooleanField(default=False)
    usuario = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE, related_name='ofertas')

    def clean(self):
        # Validar si el precio de la oferta es mayor que el precio inicial del anuncio
        if self.precio_oferta <= self.anuncio.precio_inicial:
            raise ValidationError("La oferta debe ser mayor al precio inicial del artículo.")

        # Validar si la oferta es mayor a las ofertas anteriores
        if self.id:
            ultima_oferta = self.anuncio.ofertas.exclude(id=self.id).order_by('-precio_oferta').first()
        else:
            ultima_oferta = self.anuncio.ofertas.order_by('-precio_oferta').first()

        if ultima_oferta and self.precio_oferta <= ultima_oferta.precio_oferta:
            raise ValidationError(f"La oferta debe ser mayor que la oferta más alta actual.(${ultima_oferta.precio_oferta})")

    def save(self, *args, **kwargs):
        self.clean()  # Llamamos a la validación antes de guardar
        super().save(*args, **kwargs)
