from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from store.models import Product, Variation
from .models import CartItem, Cart


# Create your views here.

# there is no card to add to when we want to add an item to card
# so we take the session_key as the primary key of the card
def _cart_id(request):
    card_id = request.session.session_key  # getting the session_key
    if not card_id:
        request.session.create()  # if it doesn't exist we create on
        card_id = request.session.session_key
    return card_id


# function to add items to the card
def add_cart(request, product_id):
    # what we are doing here:
    # 1: we are bringing the variation of the specific product we want to add to the card
    # 2: we save its variations on a list
    # 3: we bring  the card where we want to add the product and create it if it does not exist
    # 4: #we look if the product in among the card item if it is we add the new variations
    # 5: if the the item does not exist exist we create it then we add the its variations
    product = Product.objects.get(id=product_id)
    # getting the user to fix the problem of adding new product
    # instead incrementation when we add a product with same name variations
    # the cart_item is designed to user
    current_user = request.user
    if current_user.is_authenticated:
        product_variations = []
        if request.method == 'POST':
            for item in request.POST:
                # [item] is name attribute we find in html
                value = request.POST[item]
                try:
                    # to get the variations for a specific product
                    variation = Variation.objects.get(product=product, variation_category__iexact=item,
                                                      variation_value__iexact=value)
                    product_variations.append(variation)
                except:
                    pass

        # we should specify the user to get only the product related to the user
        is_card_item_exist = CartItem.objects.filter(product=product, user=current_user)
        # if the product exist in the card
        if is_card_item_exist:
            # the card may contains many items for the same products with different variations
            card_item = CartItem.objects.filter(product=product, user=current_user)  # get the product from the card
            ex_var_list = []  # a list for the variations exist for the product
            id = []  # id of the card_item
            for item in card_item:
                ex_var_list.append(list(item.variations.all()))
                id.append(item.id)
            if product_variations in ex_var_list:
                index = ex_var_list.index(
                    product_variations)  # we find at which index the product with same variations exist
                item_id = id[index]  # we retrieve the item id we the same variations
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:  # means that there is no product has the same variations
                item = CartItem.objects.create(user=current_user, product=product, quantity=1)
                if len(product_variations) > 0:
                    item.variations.clear()  # no changes detect when i commented it
                    item.variations.add(*product_variations)
                item.save()

        # if the product does not exist in the card
        else:
            card_item = CartItem.objects.create(user=current_user, product=product, quantity=1)
            if len(product_variations) > 0:
                card_item.variations.clear()  # no changes detect when i commented it
                card_item.variations.add(*product_variations)
            card_item.save()
        return redirect('cart')

    else:
        product_variations = []
        if request.method == 'POST':
            for item in request.POST:
                # [item] is name attribute we find in html
                value = request.POST[item]
                try:
                    # to get the variations for a specific product
                    variation = Variation.objects.get(product=product, variation_category__iexact=item,
                                                      variation_value__iexact=value)
                    product_variations.append(variation)
                except:
                    pass

        try:
            card = Cart.objects.get(cart_id=_cart_id(request))  # get the cart by using the session_key as id
        except Cart.DoesNotExist:
            card = Cart.objects.create(cart_id=_cart_id(request))  # create the card
        card.save()
        is_card_item_exist = CartItem.objects.filter(product=product, cart=card)
        # if the product exist in the card
        if is_card_item_exist:
            # the card may contains many items for the same products with different variations
            card_item = CartItem.objects.filter(product=product, cart=card)  # get the product from the card
            ex_var_list = []  # a list for the variations exist for the product
            id = []  # id of the card_item
            for item in card_item:
                ex_var_list.append(list(item.variations.all()))
                id.append(item.id)
            if product_variations in ex_var_list:
                index = ex_var_list.index(
                    product_variations)  # we find at which index the product with same variations exist
                item_id = id[index]  # we retrieve the item id we the same variations
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:  # means that there is no product has the same variations
                item = CartItem.objects.create(cart=card, product=product, quantity=1)
                if len(product_variations) > 0:
                    item.variations.clear()  # no changes detect when i commented it
                    item.variations.add(*product_variations)
                item.save()

        # if the product does not exist in the card
        else:
            card_item = CartItem.objects.create(cart=card, product=product, quantity=1)
            if len(product_variations) > 0:
                card_item.variations.clear()  # no changes detect when i commented it
                card_item.variations.add(*product_variations)
            card_item.save()
        return redirect('cart')


# to decrease the the quantity of product or delete it
def remove_card(request, product_id, card_item_id):
    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            card_item = CartItem.objects.get(product=product, user=request.user, id=card_item_id)
        else:
            card = Cart.objects.get(cart_id=_cart_id(request))
            card_item = CartItem.objects.get(product=product, cart=card, id=card_item_id)
        if card_item.quantity > 1:
            card_item.quantity = card_item.quantity - 1
        else:
            card_item.delete()
            return redirect('cart')
    except:
        pass
    card_item.save()
    return redirect('cart')


# to delete the product from the card
def remove_cart_item(request, product_id, card_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        card_item = CartItem.objects.get(product=product, user=request.user, id=card_item_id)
    else:
        card = Cart.objects.get(cart_id=_cart_id(request))
        card_item = CartItem.objects.get(product=product, cart=card, id=card_item_id)
    card_item.delete()
    return redirect('cart')


def cart(request, total=0, quantity=0, card_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            card_items = CartItem.objects.all().filter(user=request.user, is_active=True)
        else:
            card = Cart.objects.get(cart_id=_cart_id(request))
            card_items = CartItem.objects.filter(cart=card, is_active=True)

        for card_item in card_items:
            total += (card_item.product.price * card_item.quantity)
            quantity += card_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except:
        pass
    context = {
        'total': total,
        'quantity': quantity,
        'card_items': card_items,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'store/carts.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, card_items=None):
    global tax
    global grand_total
    try:
        if request.user.is_authenticated:
            card_items = CartItem.objects.all().filter(user=request.user, is_active=True)
        else:
            card = Cart.objects.get(cart_id=_cart_id(request))
            card_items = CartItem.objects.filter(cart=card, is_active=True)
        for card_item in card_items:
            total += (card_item.product.price * card_item.quantity)
            quantity += card_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except Exception as e:
        pass
    context = {
        'total': total,
        'quantity': quantity,
        'card_items': card_items,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, "store/checkout.html", context)
