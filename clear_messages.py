#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gareci_project.settings')
django.setup()

from reservations.models import ContactMessage

count, _ = ContactMessage.objects.all().delete()
print(f'{count} message(s) supprimé(s)')
