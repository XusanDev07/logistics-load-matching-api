from django.db import models
from django.contrib.auth.models import User
from apps.utils.base_model import AbstractBaseModel


class Driver(AbstractBaseModel):
    """
    Model representing a truck driver. It includes fields for the driver's user account,
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    home_city = models.CharField(max_length=100)
    truck_capacity_kg = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    experience_years = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} ({self.home_city})"
