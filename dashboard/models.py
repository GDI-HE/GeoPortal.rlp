from django.db import models

class SessionData(models.Model):
	sn = models.AutoField(primary_key=True)
	timestamp_create = models.DateTimeField()
	number_of_user = models.IntegerField()

	def __str__(self):
		return f"Session {self.sn} - {self.timestamp_create} - Users: {self.number_of_user}"

	class Meta:
		db_table = "session_data"
		