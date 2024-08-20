from django.db import models

class SessionData(models.Model):
	sn = models.AutoField(primary_key=True)
	timestamp_create = models.DateTimeField()
	number_of_user = models.IntegerField()

	def __str__(self):
		return f"Session {self.sn} - {self.timestamp_create} - Users: {self.number_of_user}"

	class Meta:
		db_table = "session_data"


class WMC(models.Model):
    date = models.DateField()
    wmc_id = models.IntegerField()
    wmc_public = models.IntegerField()
    wmc_title = models.CharField(max_length=255, null=True)
    mb_group_name = models.CharField(max_length=255)  # Add this field
    load_count = models.IntegerField()
    actual_load = models.IntegerField(default=0) # New column for actual load
    

    class Meta:
        ordering = ('date',)  # Sort by date