from django.db import models


class AbstractBaseModel(models.Model):
    """
    An abstract base model that provides common fields and methods for all models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__} (ID: {self.id})"
