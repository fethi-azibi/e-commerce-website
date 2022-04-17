import datetime

from django.core.mail import EmailMessage
#from django.http import JsonResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
import json
# Create your views here.
from django.template.loader import render_to_string

from carts.models import CartItem
from store.models import Product
from .forms import OrderForm
from .models import Order, Payment, OrderProduct


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # store transactions details inside payment model
    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.total,
        status=body["status"]
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # move card item to order table
    card_items = CartItem.objects.filter(user=request.user)
    for item in card_items:
        order_product = OrderProduct()
        order_product.order_id = order.id  # order_id backref
        order_product.product_id = item.product_id
        order_product.payment = order.payment
        order_product.user_id = request.user.id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()
        # we save the product first to get his id to save variations for each products(many to many field)
        order_product = OrderProduct.objects.get(id=order_product.id)
        order_product.variations.set(item.variations.all())
        order_product.save()
        # reduce quantity of the product
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # clear card items
    CartItem.objects.filter(user=request.user).delete()

    # send order received message
    mail_subject = "Thank you for your order!"
    message = render_to_string("orders/order_received_email.html",
                               {
                                   'user': request.user,
                                   'order': order,
                               })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    #send_email.send()

    data = {
        "order_number": order.order_number,
        "transID": payment.payment_id
    }

    return JsonResponse(data)


def place_order(request, total=0, quantity=0):
    current_user = request.user
    card_items = CartItem.objects.filter(user=current_user)
    # if there is no items in the card we cant place the order
    if card_items.count() < 0:
        return redirect('store')

    grand_total = 0
    for card_item in card_items:
        total += card_item.product.price * card_item.quantity
        quantity += card_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    # to save the information of the order
    if request.method == "POST":
        form = OrderForm(request.POST or None)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data.get("first_name")
            data.last_name = form.cleaned_data["last_name"]
            data.phone = form.cleaned_data["phone"]
            data.email = form.cleaned_data["email"]
            data.address_line_1 = form.cleaned_data["address_line_1"]
            data.address_line_2 = form.cleaned_data["address_line_2"]
            data.country = form.cleaned_data["country"]
            data.state = form.cleaned_data["state"]
            data.city = form.cleaned_data["city"]
            data.order_note = form.cleaned_data["order_note"]
            data.total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()  # we save here to create primary key to use it to generate order number
            # generate order number
            yr = int(datetime.date.today().strftime("%Y"))
            dy = int(datetime.date.today().strftime("%d"))
            mt = int(datetime.date.today().strftime("%m"))
            current_date = datetime.date(yr, mt, dy).strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            try:
                # order = Order.objects.filter(user=current_user, is_ordered=False, order_number=order_number).first()
                order = Order.objects.get(id=data.id)
            except Order.DoesNotExist:
                order = None
            context = {
                'order': order,
                'card_items': card_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }

            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')


def order_complete(request):

    transID = request.GET.get("payment_id")
    order_number = request.GET.get("order_number")

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for item in ordered_products:
            subtotal += item.quantity * item.product_price

        payment = Payment.objects.get(payment_id = transID)

        context = {
            "order": order,
            "ordered_products": ordered_products,
            "order_number": order.order_number,
            "transID": payment.payment_id,
            "payment": payment,
            "subtotal": subtotal
        }
        return render(request, 'orders/order_complete.html', context)
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')



