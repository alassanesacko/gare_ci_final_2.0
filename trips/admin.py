from django.contrib import admin
from .models import Trip, Bus, Category, Departure

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity')
    search_fields = ('name',)
    list_filter = ('capacity',)

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'category', 'price')
    search_fields = ('origin', 'destination')
    list_filter = ('category', 'price')

@admin.register(Departure)
class DepartureAdmin(admin.ModelAdmin):
    list_display = ('trip', 'bus', 'date', 'time', 'is_active')
    search_fields = ('trip__origin', 'trip__destination')
    list_filter = ('date', 'is_active')
