from django.contrib import admin
from .models import User, Position, Candidate, Vote

# Register your models here.

admin.site.register(User)
admin.site.register(Position)
admin.site.register(Candidate)
admin.site.register(Vote)
