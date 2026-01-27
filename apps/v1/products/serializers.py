from rest_framework import serializers
from .models import (
    MainCategory, SubCategory, Category, Product,
    ProductImage, ProductMeterage, Favourite
)


class SubCategorySerializer(serializers.ModelSerializer):
    """SubCategory serializer"""
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')


class MainCategorySerializer(serializers.ModelSerializer):
    """MainCategory serializer with subcategories"""
    sub_categories = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True, required=False, allow_null=True)
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'image', 'sub_categories')
    
    def get_sub_categories(self, obj):
        """Get all subcategories for this main category"""
        subcategories = obj.subcategories.all()
        return SubCategorySerializer(subcategories, many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    """ProductImage serializer"""
    image = serializers.ImageField(use_url=True)
    
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'is_main', 'order')


class ProductMeterageSerializer(serializers.ModelSerializer):
    """ProductMeterage serializer"""
    class Meta:
        model = ProductMeterage
        fields = ('id', 'value', 'is_active')


class CategoryInfoSerializer(serializers.ModelSerializer):
    """Category info for product"""
    main_category = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'main_category')
    
    def get_main_category(self, obj):
        if obj.parent:
            return {
                'id': obj.parent.id,
                'name': obj.parent.name
            }
        return None


class ProductSerializer(serializers.ModelSerializer):
    """Product serializer with all related data"""
    images = ProductImageSerializer(many=True, read_only=True)
    meterages = ProductMeterageSerializer(many=True, read_only=True)
    sub_category = CategoryInfoSerializer(read_only=True)
    is_favourite = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'sku', 'description', 'price_per_meter', 'stock',
            'manufacturer', 'country_of_origin', 'number_of_cores',
            'conductor_material', 'cable_cross_section', 'outer_insulation_material',
            'conductor_insulation_material', 'outer_sheath_material', 'model_version',
            'color', 'is_active', 'created_at', 'updated_at',
            'sub_category', 'images', 'meterages', 'is_favourite', 'user'
        )
    
    def get_is_favourite(self, obj):
        """Check if product is in user's favourites"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favourite.objects.filter(user=request.user, product=obj).exists()
        return False


class SupplierProductCreateUpdateSerializer(serializers.ModelSerializer):
    # Ko'p rasmlar uchun
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True
    )
    # JSON stringni obyektga aylantirish uchun JSONField ishlatamiz
    meterages = serializers.JSONField(
        required=False, 
        write_only=True,
        help_text='Format: [{"value": 10, "is_active": true}]'
    )

    class Meta:
        model = Product
        fields = (
            'sub_category', 'name', 'sku', 'description', 'price_per_meter', 'stock',
            'manufacturer', 'country_of_origin', 'number_of_cores',
            'conductor_material', 'cable_cross_section', 'outer_insulation_material',
            'conductor_insulation_material', 'outer_sheath_material', 'model_version',
            'color', 'is_active', 'images', 'meterages'
        )

    def validate_sku(self, value):
        qs = Product.objects.filter(sku=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Товар с таким артикулом уже существует")
        return value

    def validate_meterages(self, value):
        # Agar Swagger yoki Postman'dan string bo'lib kelsa, uni parse qilamiz
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError("Invalid JSON format for meterages")
        return value

    def _save_related_data(self, product, images_data, meterages_data, is_update=False):
        # Rasmlarni saqlash
        if images_data is not None:
            if is_update:
                product.images.all().delete()
            for idx, image in enumerate(images_data):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_main=(idx == 0),
                    order=idx
                )

        # Metrajlarni saqlash
        if meterages_data is not None:
            if is_update:
                product.meterages.all().delete()
            for m_data in meterages_data:
                ProductMeterage.objects.create(
                    product=product,
                    value=m_data.get('value'),
                    is_active=m_data.get('is_active', True)
                )

    def create(self, validated_data):
        images_data = validated_data.pop('images', None)
        meterages_data = validated_data.pop('meterages', None)
        validated_data['user'] = self.context['request'].user
        
        product = Product.objects.create(**validated_data)
        self._save_related_data(product, images_data, meterages_data)
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        meterages_data = validated_data.pop('meterages', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        self._save_related_data(instance, images_data, meterages_data, is_update=True)
        return instance
