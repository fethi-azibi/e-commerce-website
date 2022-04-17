import requests
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from accounts.models import Account, UserProfile
from carts.models import Cart, CartItem
from carts.views import _cart_id
from .forms import RegistrationForm, UserForm, UserProfileForm
from orders.models import Order, OrderProduct

# Create your views here.

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            phone_number = form.cleaned_data.get('phone')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get("password")
            username = email.split("@")[0]
            user = Account.objects.create_user(last_name=last_name, first_name=first_name,
                                               username=username, password=password, email=email)
            user.phone = phone_number
            user.save()

            # sending email configuration for user activation
            current_site = get_current_site(request)  # to get our domain name
            mail_subject = "Please Activate your account"  # the mail subject
            message = render_to_string("accounts/account_verification_email.html", {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()
            return redirect('/accounts/login/?command=verification&email=' + email)
    else:
        form = RegistrationForm()
    context = {"form": form}
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email, password=password)
        if user:
            try:
                card = Cart.objects.get(cart_id=_cart_id(request))
                # getting the items of the card
                # and saving their variations
                is_card_item_exists = CartItem.objects.filter(cart=card).exists()
                if is_card_item_exists:
                    card_item = CartItem.objects.filter(cart=card)
                    # getting the products variations
                    product_variations = []
                    for item in card_item:
                        variation = item.variations.all()
                        product_variations.append(list(variation))
                    # getting the card items from the user
                    card_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in card_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    for pr in product_variations:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            card_item = CartItem.objects.filter(card=card)
                            for item in card_item:
                                item.user = user
                                item.save()

            except:
                pass
            auth.login(request, user)
            # this function returns the full url http://127.0.0.1/checkout/cart
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query  # return next=cart/checkout
                print('query-->', query)
                print('query split 0 ->', query.split('&'))  # we make .split('&') to convert the string to a list
                # print('query split 1->', query.split('&')[1])
                params = dict(x.split("=") for x in query.split('&'))  # {next: cart/checkout}
                if 'next' in params:
                    next_page = params['next']
                    return redirect(next_page)
            except:
                return redirect('dashboard')

        else:
            return redirect('login')
    return render(request, 'accounts/login.html')


def activate(request, uid, token):
    try:
        decoded_uid = urlsafe_base64_decode(uid).decode()
        user = Account._default_manager.get(pk=decoded_uid)
    except (TypeError, ValueError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return HttpResponse('Invalid activation link')


@login_required(login_url='login')
def dashboard(request):
    orders_count = Order.objects.order_by("-created_at").filter(user_id=request.user.id, is_ordered=True).count()
    user_profile = UserProfile.objects.get(user_id=request.user.id)
    context={
        'orders_count':orders_count,
        'user_profile':user_profile,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def logout(request):
    auth.logout(request)
    return redirect('login')


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            # sending email configuration for user activation
            current_site = get_current_site(request)  # to get our domain name
            mail_subject = "Please Activate your account"  # the mail subject
            message = render_to_string("accounts/reset_forgot_password.html", {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()
            return redirect('login')
        else:
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uid, token):
    try:
        uid = urlsafe_base64_decode(uid).decode()
        user = Account._default_manager.get(pk=uid)
    except(ValueError, TypeError, OverflowError):
        user = None

    if user and default_token_generator.check_token(user, token):
        request.session['uid'] = uid  # we save the user id in our session to use it in resetPassword
        return redirect('resetPassword')
    else:
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session['uid']
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            return redirect('login')
        else:
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')

@login_required(login_url="login")
def my_orders(request):
    orders = Order.objects.order_by("-created_at").filter(user_id=request.user.id, is_ordered=True)
    context={
        'orders':orders
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url="login")
def edit_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        #when we have a file ina  form we use request.FILES
        profile_form = UserProfileForm(request.POST,request.FILES, instance=user_profile) 
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_profile': user_profile,
    }
    
    return render(request, 'accounts/edit_profile.html', context)
@login_required(login_url="login")
def change_password(request):
    if request.method == "POST":
        user = Account.objects.get(username__exact=request.user.username)
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if new_password == confirm_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                #auth.logout(user)   if we want to logout after setting the password
            else:
                return redirect('change_password')
        else:
            return redirect('change_password')
    return render(request, "accounts/change_password.html")

def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.quantity * i.product_price
    context = {
        'order':order,
        'order_detail': order_detail,
        'subtotal': subtotal
    }
    
    return render(request, "accounts/order_detail.html", context)