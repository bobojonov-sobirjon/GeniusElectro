from rest_framework import serializers

from django.contrib.auth import authenticate

from django.contrib.auth.password_validation import validate_password

from .models import CustomUser, Company, CompanyDocument, LegalFormType, ActsOnBasisType





class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    password_confirm = serializers.CharField(write_only=True, required=True)



    class Meta:

        model = CustomUser

        fields = ('email', 'first_name', 'last_name', 'phone', 'password', 'password_confirm')



    def validate(self, attrs):

        if attrs['password'] != attrs['password_confirm']:

            raise serializers.ValidationError({"password": "Пароли не совпадают"})

        return attrs



    def validate_email(self, value):

        if CustomUser.objects.filter(email=value).exists():

            raise serializers.ValidationError("Пользователь с таким email уже существует")

        return value



    def validate_phone(self, value):

        if CustomUser.objects.filter(phone=value).exists():

            raise serializers.ValidationError("Пользователь с таким номером телефона уже существует")

        return value



    def create(self, validated_data):

        validated_data.pop('password_confirm')

        # Use email as username

        user = CustomUser.objects.create_user(

            email=validated_data['email'],

            username=validated_data['email'],  # Set username to email

            first_name=validated_data['first_name'],

            last_name=validated_data['last_name'],

            phone=validated_data['phone'],

            password=validated_data['password'],

            is_active=True,

            is_email_verified=False

        )

        return user





class LoginSerializer(serializers.Serializer):

    email_or_phone = serializers.CharField(required=True)

    password = serializers.CharField(write_only=True, required=True)



    def validate(self, attrs):

        email_or_phone = attrs.get('email_or_phone')

        password = attrs.get('password')



        if not email_or_phone or not password:

            raise serializers.ValidationError("Необходимо указать email/телефон и пароль")



        user = None

        if '@' in email_or_phone:

            try:

                user = CustomUser.objects.get(email=email_or_phone)

            except CustomUser.DoesNotExist:

                raise serializers.ValidationError("Неверный email или пароль")

        else:

            try:

                user = CustomUser.objects.get(phone=email_or_phone)

            except CustomUser.DoesNotExist:

                raise serializers.ValidationError("Неверный номер телефона или пароль")



        if not user.check_password(password):

            raise serializers.ValidationError("Неверный email/телефон или пароль")



        if not user.is_active:

            raise serializers.ValidationError("Аккаунт деактивирован")



        attrs['user'] = user

        return attrs





class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:

        model = CustomUser

        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'is_email_verified', 'created_at', 'updated_at',

                  'city', 'street', 'flat', 'house', 'index')

        read_only_fields = ('id', 'email', 'is_email_verified', 'created_at', 'updated_at')





class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:

        model = CustomUser

        fields = ('first_name', 'last_name', 'city', 'street', 'flat', 'house', 'index')

        read_only_fields = ('phone', 'email')





class ForgotPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)



    def validate_email(self, value):

        if not CustomUser.objects.filter(email=value).exists():

            raise serializers.ValidationError("Пользователь с таким email не найден")

        return value





class PasswordResetSerializer(serializers.Serializer):

    token = serializers.CharField(required=True)

    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    new_password_confirm = serializers.CharField(write_only=True, required=True)



    def validate(self, attrs):

        if attrs['new_password'] != attrs['new_password_confirm']:

            raise serializers.ValidationError({"new_password": "Пароли не совпадают"})

        return attrs





class PasswordChangeSerializer(serializers.Serializer):

    old_password = serializers.CharField(write_only=True, required=True)

    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    new_password_confirm = serializers.CharField(write_only=True, required=True)



    def validate_old_password(self, value):

        user = self.context['request'].user

        if not user.check_password(value):

            raise serializers.ValidationError("Неверный текущий пароль")

        return value



    def validate(self, attrs):

        if attrs['new_password'] != attrs['new_password_confirm']:

            raise serializers.ValidationError({"new_password": "Пароли не совпадают"})

        return attrs





class RegisterSupplierSerializer(serializers.Serializer):

    """Serializer for supplier registration"""

    name_company = serializers.CharField(max_length=255, required=True, write_only=True)

    first_name = serializers.CharField(max_length=150, required=True)

    last_name = serializers.CharField(max_length=150, required=True)

    phone = serializers.CharField(max_length=20, required=True)

    email = serializers.EmailField(required=True)

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    password_confirm = serializers.CharField(write_only=True, required=True)



    def validate_email(self, value):

        if CustomUser.objects.filter(email=value).exists():

            raise serializers.ValidationError("Пользователь с таким email уже существует")

        return value



    def validate_phone(self, value):

        if CustomUser.objects.filter(phone=value).exists():

            raise serializers.ValidationError("Пользователь с таким номером телефона уже существует")

        return value



    def validate(self, attrs):

        if attrs['password'] != attrs['password_confirm']:

            raise serializers.ValidationError({"password": "Пароли не совпадают"})

        return attrs



    def create(self, validated_data):

        password_confirm = validated_data.pop('password_confirm')

        name_company = validated_data.pop('name_company')

        

        # Create user

        user = CustomUser.objects.create_user(

            email=validated_data['email'],

            username=validated_data['email'],  # Set username to email

            first_name=validated_data['first_name'],

            last_name=validated_data['last_name'],

            phone=validated_data['phone'],

            password=validated_data['password'],

            is_active=True,

            is_email_verified=False

        )

        

        # Create company and link to user

        company = Company.objects.create(

            user=user,

            name_company=name_company

        )

        

        return user





class CompanyDocumentSerializer(serializers.ModelSerializer):

    """Serializer для Company documents с отдельными полями для файлов
    
    Включает следующие документы:
    - tin_certificate: Свидетельство о постановке на налоговый учет (ИНН)
    - ogrn_certificate: Свидетельство ОГРН/ОГРИП
    - charter: Устав компании
    - director_appointment: Приказ о назначении директора
    """
    
    class Meta:
        model = CompanyDocument
        fields = (
            'id', 'company', 'tin_certificate', 'ogrn_certificate', 
            'charter', 'director_appointment', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')





class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer для Company со всеми полями
    
    Включает полную информацию о компании:
    - Юридические реквизиты (ИНН, ОГРН, КПП и т.д.)
    - Адреса (юридический и фактический)
    - Банковские реквизиты
    - Контактную информацию
    - Данные директора
    - Связанные документы
    """

    organizational_legal_form_display = serializers.SerializerMethodField(
        help_text="Отображаемое название организационно-правовой формы"
    )

    acts_on_basis_display = serializers.SerializerMethodField(
        help_text="Отображаемое название основания действий"
    )

    documents = CompanyDocumentSerializer(many=True, read_only=True, help_text="Документы компании")

    

    class Meta:

        model = Company

        fields = (

            'id', 'user', 'name_company', 'organizational_legal_form', 'organizational_legal_form_display',

            'abbreviated_name', 'full_name', 'inn', 'ogrn_ogrnip', 'kpp', 'okpo', 'registration_date',

            'legal_index', 'legal_region', 'legal_city', 'legal_street', 'legal_house', 'legal_building', 'legal_office',

            'matches_legal_address', 'actual_index', 'actual_region', 'actual_city', 'actual_street',

            'actual_house', 'actual_building', 'actual_office',

            'bank_name', 'bic', 'settlement_account', 'correspondent_account',

            'contact_person_full_name', 'position', 'phone_number', 'email',

            'director_full_name', 'director_position', 'acts_on_basis', 'acts_on_basis_display',

            'documents', 'created_at', 'updated_at'

        )

        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    

    def get_organizational_legal_form_display(self, obj):

        """Return Russian display name for organizational_legal_form"""

        if obj.organizational_legal_form:

            return dict(LegalFormType.choices).get(obj.organizational_legal_form, obj.organizational_legal_form)

        return None

    

    def get_acts_on_basis_display(self, obj):

        """Return Russian display name for acts_on_basis"""

        if obj.acts_on_basis:

            return dict(ActsOnBasisType.choices).get(obj.acts_on_basis, obj.acts_on_basis)

        return None



class CompanyUpdateSerializer(serializers.ModelSerializer):
    """Kompaniya ma'lumotlarini tahrirlash uchun serializer"""
    class Meta:
        model = Company
        fields = [
            'name_company', 'organizational_legal_form', 'abbreviated_name', 
            'full_name', 'inn', 'ogrn_ogrnip', 'kpp', 'okpo', 
            'registration_date', 'legal_index', 'legal_region', 'legal_city', 
            'legal_street', 'legal_house', 'legal_building', 'legal_office', 
            'matches_legal_address', 'actual_index', 'actual_region', 
            'actual_city', 'actual_street', 'actual_house', 'actual_building', 
            'actual_office', 'bank_name', 'bic', 'settlement_account', 
            'correspondent_account', 'contact_person_full_name', 'position', 
            'phone_number', 'email', 'director_full_name', 
            'director_position', 'acts_on_basis'
        ]


class CompanyDocumentSerializer(serializers.ModelSerializer):
    """Kompaniya hujjatlari uchun serializer"""
    class Meta:
        model = CompanyDocument
        fields = [
            'tin_certificate', 'ogrn_certificate', 
            'charter', 'director_appointment'
        ]