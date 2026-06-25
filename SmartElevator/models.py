from django.db import models

class Elevator(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=10)
    current_floor = models.IntegerField(default=0)
    direction = models.CharField(max_length=10, default="IDLE")
    is_moving = models.BooleanField(default=False)
    is_emergency = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class UserRequest(models.Model):
    id = models.AutoField(primary_key=True)
    source_floor = models.IntegerField()
    destination_floor = models.IntegerField()
    elevator = models.ForeignKey(Elevator, null=True, on_delete=models.SET_NULL)
    direction = models.CharField(max_length=10)
    status = models.CharField(max_length=10,choices=[
        ("PENDING", "PENDING"),
        ("COMPLETED", "COMPLETED"),
    ]
    , default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)