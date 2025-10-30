from django.db import models

class StripeEvent(models.Model):
    """
    Store processed Stripe event IDs for idempotency.
    """
    event_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
