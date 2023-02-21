from django.db import models


# Create your models here.
class Tracking(models.Model):
    _id=models.AutoField(primary_key=True, editable=False)
    tracking_number = models.CharField(max_length=50, blank=False)
    order_number = models.CharField(max_length=50, blank=False)
    create_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_number}"
    

class BlackListed(models.Model):
    word = models.CharField(max_length=70, blank=False)
    replace_word = models.CharField(max_length=70, blank=False)
    create_at = models.DateField(auto_now_add=True)
    def __str__(self):
        return f"{self.word}"