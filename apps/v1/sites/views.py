from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Contact, Partner, Request
from .serializers import ContactSerializer, PartnerSerializer, RequestCreateSerializer


@extend_schema(
    tags=['Контактная информация'],
    summary='Получить контактную информацию',
    description='Возвращает контактную информацию (адрес, телефон, email, режим работы, карта)',
    responses={200: ContactSerializer, 404: OpenApiTypes.OBJECT}
)
class ContactAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get contact information"""
        try:
            contact = Contact.objects.first()
            if not contact:
                return Response({
                    'error': 'Контактная информация не найдена'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ContactSerializer(contact, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Партнеры'],
    summary='Получить список партнеров',
    description='Возвращает список всех партнеров с их изображениями',
    responses={200: PartnerSerializer(many=True)}
)
class PartnerListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all partners"""
        partners = Partner.objects.all().order_by('-created_at')
        serializer = PartnerSerializer(partners, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Заявки'],
    summary='Оставить заявку',
    description='Создает новую заявку. Пользователь может оставить заявку с контактными данными, комментарием и прикрепленным файлом.',
    request={
        'multipart/form-data': RequestCreateSerializer,
        'application/json': RequestCreateSerializer,
    },
    responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
)
class RequestCreateAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        """Create a new request"""
        serializer = RequestCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        request_obj = serializer.save()
        
        return Response({
            'message': 'Заявка успешно отправлена',
            'id': request_obj.id
        }, status=status.HTTP_201_CREATED)
