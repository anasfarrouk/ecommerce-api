import stripe
import json
from decimal import Decimal
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.db import transaction

from .models import OrderModel, CartItemModel, ProductModel

stripe.api_key = settings.STRIPE_SECRET_KEY
WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET  # set this from env

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        return HttpResponseBadRequest("Invalid payload")
    except stripe.error.SignatureVerificationError:
        return HttpResponseForbidden("Invalid signature")

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")
        # Prefer metadata.order_id if present
        order_id = session.get("metadata", {}).get("order_id")
        try:
            if order_id:
                order = OrderModel.objects.select_for_update().get(id=order_id)
            else:
                order = OrderModel.objects.select_for_update().get(stripe_session_id=session_id)
        except OrderModel.DoesNotExist:
            # Unknown order — log and ack
            return HttpResponse(status=200)

        # idempotent update: only act if not already paid
        if not order.paid:
            with transaction.atomic():
                # mark paid
                order.paid = True
                order.save(update_fields=["paid"])

                # decrement stock (optional) and ensure sufficient quantity
                items = CartItemModel.objects.filter(cart=order.cart).select_related("product").select_for_update()
                for it in items:
                    prod = it.product
                    if prod.stock_quantity < it.quantity:
                        # handle insufficient stock: flag, notify, or raise
                        # here we set paid=False and optionally create refund flow
                        # for simplicity, set paid=False and continue
                        order.paid = False
                        order.save(update_fields=["paid"])
                        # In production: create refund, alert admins, or restock logic
                        return HttpResponse(status=200)
                    prod.stock_quantity -= it.quantity
                    prod.save(update_fields=["stock_quantity"])

    # Optionally handle payment_intent.succeeded / checkout.session.async_payment_succeeded etc.
    return HttpResponse(status=200)

