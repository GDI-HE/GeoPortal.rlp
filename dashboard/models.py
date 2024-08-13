from django.db import models

class SESSION_USER(models.Model):
    id = models.AutoField(primary_key=True)
    datetime = models.DateTimeField()
    session_number = models.IntegerField()

    def __str__(self):
        return f"{self.id} - {self.datetime} - {self.session_number}"