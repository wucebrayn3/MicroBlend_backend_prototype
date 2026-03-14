from rest_framework import viewsets
from .models import TableSession
from .serializers import TableSessionSerializer

class TableSessionViewSet(viewsets.ModelViewSet):
    queryset = TableSession.objects.all()
    serializer_class = TableSessionSerializer