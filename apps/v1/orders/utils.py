"""
Utility functions for orders app
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_order_status_sms(order, new_status, order_product=None):
    """
    Send SMS notification to order creator when order product status changes
    
    Args:
        order: Order instance
        new_status: New status value (Ожидание, Обрабатывается, Отправлен)
        order_product: OrderProduct instance (optional, if None, sends for all products)
    """
    try:
        user = order.user
        phone = user.phone
        
        if not phone:
            logger.warning(f"User {user.id} does not have a phone number for SMS")
            return
        
        # Status display names
        status_names = {
            'Ожидание': 'Ожидание',
            'Обрабатывается': 'Обрабатывается',
            'Отправлен': 'Отправлен'
        }
        
        status_display = status_names.get(new_status, new_status)
        
        # If order_product is specified, send SMS for that specific product
        if order_product:
            product_name = f"{order_product.product.name} ({order_product.quantity} м)"
            
            # SMS message for specific product
            message = f"""Здравствуйте, {user.first_name}!

Статус товара "{product_name}" в заказе #{order.id} изменен на "{status_display}".

Сумма заказа: {order.total_price} ₽

С уважением,
GeniusElectro"""
        else:
            # Get product names from order
            product_names = []
            for op in order.order_products.all():
                product_names.append(f"{op.product.name} ({op.quantity} м)")
            
            products_text = ", ".join(product_names[:3])  # First 3 products
            if len(product_names) > 3:
                products_text += f" и еще {len(product_names) - 3} товар(ов)"
            
            # SMS message for all products
            message = f"""Здравствуйте, {user.first_name}!

Статус вашего заказа #{order.id} изменен на "{status_display}".

Товары в заказе: {products_text}

Сумма заказа: {order.total_price} ₽

С уважением,
GeniusElectro"""
        
        # TODO: Integrate with your SMS service provider
        # Example integrations:
        # - Twilio
        # - SMS.ru
        # - Any other SMS gateway
        
        # For now, we'll log the SMS (you can replace this with actual SMS sending)
        logger.info(f"SMS to {phone}: {message}")
        
        # Example SMS sending (uncomment and configure your SMS service):
        # from your_sms_service import send_sms
        # send_sms(phone, message)
        
        # Or use a library like:
        # import requests
        # response = requests.post(
        #     'https://your-sms-gateway.com/api/send',
        #     data={
        #         'phone': phone,
        #         'message': message,
        #         'api_key': settings.SMS_API_KEY
        #     }
        # )
        
    except Exception as e:
        logger.error(f"Error sending SMS for order {order.id}: {str(e)}")
        raise
