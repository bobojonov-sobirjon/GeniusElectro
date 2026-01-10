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
            'sub_category', 'images', 'meterages', 'is_favourite'
        )
    
    def get_is_favourite(self, obj):
        """Check if product is in user's favourites"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favourite.objects.filter(user=request.user, product=obj).exists()
        return False
