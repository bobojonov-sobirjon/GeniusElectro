from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, LoginSerializer, UserDetailSerializer,
    UserUpdateSerializer, ForgotPasswordSerializer, PasswordResetSerializer,
    PasswordChangeSerializer
)
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
