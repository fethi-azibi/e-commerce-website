from .models import CartItem, Cart
from .views import _cart_id


def counter(request):
    card_count = 0
    try:
        if request.user.is_authenticated:
            card_items = CartItem.objects.all().filter(user=request.user, is_active=True)
        else:
            card = Cart.objects.filter(cart_id=_cart_id(request))
            # print(card[0])
            # filter returns a list of objects that is why we need to specify the object we want
            card_items = CartItem.objects.all().filter(cart=card[:1])
        for card_item in card_items:
            card_count = card_count + card_item.quantity
    except:
        card_count = 0
    return dict(card_count=card_count)
