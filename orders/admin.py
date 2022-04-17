from django.contrib import admin
from .models import Payment, Order, OrderProduct


# to link OrderProduct to Order when we click to order we will see order products
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0  # django gives 3 extra empty table , by make it 0 will not appear


class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "full_name", "phone", "email", "city", "total", "tax", "is_ordered",
                    "created_at"]
    list_filter = ["is_ordered",]
    search_fields = ["email", "order_number", "first_name", "last_name"]
    list_per_page = 20
    inlines = [OrderProductInline, ]


# Register your models here.
admin.site.register(Payment)
admin.site.register(OrderProduct)
admin.site.register(Order, OrderAdmin)
