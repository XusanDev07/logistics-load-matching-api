from django.db import models
from django.contrib.auth.models import User
from apps.utils.base_model import AbstractBaseModel


class Load(AbstractBaseModel):
    """
    Model representing a load that needs to be transported. It includes fields for the load's details,
    """

    class Status(models.TextChoices):
        POSTED = 'POSTED', 'Posted'
        MATCHED = 'MATCHED', 'Matched'
        COMPLETED = 'COMPLETED', 'Completed'

    company = models.ForeignKey(User, on_delete=models.CASCADE)
    pickup_city = models.CharField(max_length=100)
    delivery_city = models.CharField(max_length=100)
    weight_kg = models.PositiveIntegerField()
    pickup_date = models.DateField()
    max_budget = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.POSTED)

    def __str__(self):
        return f"Load {self.id} from {self.pickup_city} to {self.delivery_city}"
