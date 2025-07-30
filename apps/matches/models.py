from django.db import models
from apps.drivers.models import Driver
from apps.loads.models import Load
from apps.utils.base_model import AbstractBaseModel


class LoadMatch(AbstractBaseModel):
    """
    Model representing a match between a load and a driver, including details
    about the distance category and match score.
    """

    class DistanceChoices(models.TextChoices):
        SAME_CITY = 'SAME_CITY', 'Same City'
        NEARBY = 'NEARBY', 'Nearby'
        REGIONAL = 'REGIONAL', 'Regional'
        LONG_DISTANCE = 'LONG_DISTANCE', 'Long Distance'

    load = models.ForeignKey(Load, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    distance_category = models.CharField(max_length=20, choices=DistanceChoices.choices)
    match_score = models.FloatField()

    def __str__(self):
        return f"Match: Load {self.load.id} -> Driver {self.driver.user.username}"
