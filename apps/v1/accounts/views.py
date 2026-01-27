from rest_framework import status

from rest_framework.views import APIView

from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.response import Response

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiParameter

from drf_spectacular.types import OpenApiTypes

from .models import CustomUser, EmailVerificationToken, PasswordResetToken, Company, CompanyDocument

from .serializers import (
    RegisterSerializer, RegisterSupplierSerializer, LoginSerializer, UserDetailSerializer,
    UserUpdateSerializer, ForgotPasswordSerializer, PasswordResetSerializer,
    PasswordChangeSerializer, CompanySerializer, CompanyDocumentSerializer, CompanyUpdateSerializer
)

from django.shortcuts import get_object_or_404

from .utils import (
    send_verification_email, send_password_reset_email,

    create_email_verification_token, create_password_reset_token

)





@extend_schema(

    tags=['Аутентификация'],

    request=RegisterSerializer,

    responses={201: RegisterSerializer, 400: OpenApiTypes.OBJECT}

)

class RegisterAPIView(APIView):

    permission_classes = [AllowAny]



    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()

            verification_token = create_email_verification_token(user)

            send_verification_email(user, verification_token.token)

            

            return Response({

                'message': 'Регистрация успешна. Пожалуйста, проверьте вашу почту для подтверждения email.'

            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(

    tags=['Аутентификация'],

    request=RegisterSupplierSerializer,

    responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},

    summary='Регистрация поставщика',

    description='Регистрация нового поставщика с созданием компании. Требуются: название компании, имя, фамилия, телефон, email и пароль.'

)

class RegisterSupplierAPIView(APIView):

    permission_classes = [AllowAny]



    def post(self, request):

        serializer = RegisterSupplierSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()

            verification_token = create_email_verification_token(user)

            send_verification_email(user, verification_token.token)

            

            return Response({

                'message': 'Регистрация поставщика успешна. Пожалуйста, проверьте вашу почту для подтверждения email.',

                'user_id': user.id,

                'company_id': user.companies.first().id if user.companies.exists() else None

            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(

    tags=['Аутентификация'],

    request=LoginSerializer,

    responses={200: LoginSerializer, 400: OpenApiTypes.OBJECT}

)

class LoginAPIView(APIView):

    permission_classes = [AllowAny]



    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)

            return Response({

                'message': 'Вход выполнен успешно',

                'user': {

                    'id': user.id,

                    'email': user.email,

                    'first_name': user.first_name,

                    'last_name': user.last_name,

                    'phone': user.phone,

                    'is_email_verified': user.is_email_verified

                },

                'tokens': {

                    'refresh': str(refresh),

                    'access': str(refresh.access_token)

                }

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(

    tags=['Пользователь'],

    responses={200: UserDetailSerializer}

)

class UserDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]



    def get(self, request):

        serializer = UserDetailSerializer(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)



    @extend_schema(

        request=UserUpdateSerializer,

        responses={200: UserDetailSerializer, 400: OpenApiTypes.OBJECT}

    )

    def put(self, request):

        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():

            serializer.save()

            request.user.refresh_from_db()

            user_serializer = UserDetailSerializer(request.user)

            return Response({

                'message': 'Данные пользователя обновлены',

                'user': user_serializer.data

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(

    tags=['Аутентификация'],

    parameters=[

        OpenApiParameter('token', OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Токен подтверждения email')

    ],

    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}

)

class VerifyEmailAPIView(APIView):

    permission_classes = [AllowAny]



    def get(self, request):

        token = request.GET.get('token')

        if not token:

            return Response({

                'error': 'Токен не предоставлен'

            }, status=status.HTTP_400_BAD_REQUEST)

        

        try:

            verification_token = EmailVerificationToken.objects.select_related('user').get(token=token, is_used=False)

            

            if verification_token.is_expired():

                return Response({

                    'error': 'Срок действия ссылки истек. Пожалуйста, запросите новую ссылку для подтверждения.'

                }, status=status.HTTP_400_BAD_REQUEST)

            

            user = verification_token.user

            user.is_email_verified = True

            user.save()

            

            verification_token.is_used = True

            verification_token.save()

            

            return Response({

                'message': 'Email успешно подтвержден'

            }, status=status.HTTP_200_OK)

        

        except EmailVerificationToken.DoesNotExist:

            return Response({

                'error': 'Неверная или уже использованная ссылка подтверждения'

            }, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(

    tags=['Аутентификация'],

    request=ForgotPasswordSerializer,

    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}

)

class ForgotPasswordAPIView(APIView):

    permission_classes = [AllowAny]



    def post(self, request):

        serializer = ForgotPasswordSerializer(data=request.data)

        if serializer.is_valid():

            email = serializer.validated_data['email']

            user = CustomUser.objects.get(email=email)

            reset_token = create_password_reset_token(user)

            send_password_reset_email(user, reset_token.token)

            

            return Response({

                'message': 'Инструкции по сбросу пароля отправлены на ваш email'

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(

    tags=['Аутентификация'],

    request=PasswordResetSerializer,

    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}

)

class ResetPasswordAPIView(APIView):

    permission_classes = [AllowAny]



    def post(self, request):

        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():

            token = serializer.validated_data['token']

            new_password = serializer.validated_data['new_password']

            

            try:

                reset_token = PasswordResetToken.objects.select_related('user').get(token=token, is_used=False)

                

                if reset_token.is_expired():

                    return Response({

                        'error': 'Срок действия ссылки истек. Пожалуйста, запросите новую ссылку для сброса пароля.'

                    }, status=status.HTTP_400_BAD_REQUEST)

                

                user = reset_token.user

                user.set_password(new_password)

                user.save()

                

                reset_token.is_used = True

                reset_token.save()

                

                PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

                

                return Response({

                    'message': 'Пароль успешно изменен'

                }, status=status.HTTP_200_OK)

            

            except PasswordResetToken.DoesNotExist:

                return Response({

                    'error': 'Неверная или уже использованная ссылка для сброса пароля'

                }, status=status.HTTP_400_BAD_REQUEST)

        

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(

    tags=['Пользователь'],

    request=PasswordChangeSerializer,

    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}

)

class ChangePasswordAPIView(APIView):

    permission_classes = [IsAuthenticated]



    def post(self, request):

        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():

            user = request.user

            new_password = serializer.validated_data['new_password']

            user.set_password(new_password)

            user.save()

            

            return Response({

                'message': 'Пароль успешно изменен'

            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





# Company API Views

@extend_schema(

    tags=['Компания'],

    summary='Получить компанию текущего пользователя',

    description='Возвращает информацию о компании, связанной с текущим аутентифицированным пользователем. Требуется аутентификация.',

    responses={200: CompanySerializer, 404: OpenApiTypes.OBJECT}

)

class CompanyDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    

    def get(self, request):

        """Get current user's company"""

        try:

            company = Company.objects.select_related('user').prefetch_related('documents').get(user=request.user)

            serializer = CompanySerializer(company, context={'request': request})

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Company.DoesNotExist:

            return Response({

                'error': 'Компания не найдена'

            }, status=status.HTTP_404_NOT_FOUND)





@extend_schema(

    tags=['Компания'],

    summary='Получить компанию по ID',

    description='Возвращает информацию о компании по указанному ID. Требуется аутентификация.',

    responses={200: CompanySerializer, 404: OpenApiTypes.OBJECT},

    parameters=[

        OpenApiParameter(

            name='id',

            type=OpenApiTypes.INT,

            location=OpenApiParameter.PATH,

            description='ID компании',

            required=True

        )

    ]

)

class CompanyByIdAPIView(APIView):

    permission_classes = [IsAuthenticated]

    

    def get(self, request, id):

        """Get company by ID"""

        try:

            company = Company.objects.select_related('user').prefetch_related('documents').get(id=id)

            serializer = CompanySerializer(company, context={'request': request})

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Company.DoesNotExist:

            return Response({

                'error': 'Компания не найдена'

            }, status=status.HTTP_404_NOT_FOUND)



class CompanyUpdateAPIView(APIView):
    """Kompaniya ma'lumotlarini PUT orqali tahrirlash"""
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="Обновление данных компании",
        description="Обновление основной информации о компании. Используйте multipart/form-data.",
        request=CompanyUpdateSerializer,
        responses={
            200: CompanyUpdateSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        tags=["Компания"]
    )
    def put(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        serializer = CompanyUpdateSerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentAPIView(APIView):
    """Kompaniya hujjatlarini POST va PUT qilish"""
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="Загрузка документов компании",
        description="Первичная загрузка файлов документов (ИНН, ОГРН и т.д.)",
        request=CompanyDocumentSerializer,
        responses={
            201: CompanyDocumentSerializer,
            400: OpenApiTypes.OBJECT
        },
        tags=["Документы компании"]
    )
    def post(self, request, company_id):
        company = get_object_or_404(Company, id=company_id)
        serializer = CompanyDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(company=company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Обновление документов компании",
        description="Обновление ранее загруженных документов компании. "
                    "Можно обновить один или несколько документов.",
        request=CompanyDocumentSerializer,
        responses={
            200: CompanyDocumentSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        tags=["Документы компании"]
    )
    def put(self, request, company_id):
        document = get_object_or_404(CompanyDocument, company_id=company_id)
        serializer = CompanyDocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    """
    API для управления документами компании
    
    Позволяет загружать и обновлять документы компании:
    - Свидетельство о постановке на налоговый учет (ИНН)
    - Свидетельство ОГРН/ОГРИП
    - Устав компании
    - Приказ о назначении директора
    """
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="Загрузка документов компании",
        description="Загрузка официальных документов компании. "
                   "Поддерживаются форматы PDF, JPG, PNG. "
                   "Максимальный размер файла: 10MB.",
        request=CompanyDocumentSerializer,
        responses={
            201: CompanyDocumentSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        tags=["Документы компании"]
    )
    def post(self, request, company_id):
        """
        Загрузить документы компании
        
        Args:
            company_id: ID компании для загрузки документов
            
        Returns:
            201: Созданные документы
            400: Ошибки валидации
            404: Компания не найдена
        """
        company = get_object_or_404(Company, id=company_id)
        serializer = CompanyDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(company=company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Обновление документов компании",
        description="Обновление ранее загруженных документов компании. "
                   "Можно обновить один или несколько документов.",
        request=CompanyDocumentSerializer,
        responses={
            200: CompanyDocumentSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        tags=["Документы компании"]
    )
    def put(self, request, company_id):
        """
        Обновить документы компании
        
        Args:
            company_id: ID компании для обновления документов
            
        Returns:
            200: Обновленные документы
            400: Ошибки валидации
            404: Документы или компания не найдены
        """
        # Находим документы компании
        document = get_object_or_404(CompanyDocument, company_id=company_id)
        serializer = CompanyDocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)