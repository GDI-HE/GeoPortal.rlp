from django.db import models

class SessionData(models.Model):
    sn = models.AutoField(primary_key=True)
    timestamp_create = models.DateTimeField()
    number_of_user = models.IntegerField()

    def __str__(self):
        return f"Session {self.sn} - {self.timestamp_create} - Users: {self.number_of_user}"

    class Meta:
        db_table = "session_data"


class SESSION_USER(models.Model):
    datetime = models.DateTimeField()
    session_number = models.IntegerField()

    def __str__(self):
        return f"{self.datetime} - {self.session_number}"
    
    class Meta:
        db_table = "dashboard_session_user"

class MbUserDeletion(models.Model):
    id = models.AutoField(primary_key=True)
    mb_user_id = models.IntegerField()
    mb_user_name = models.CharField(max_length=255)
    mb_user_email = models.CharField(max_length=255)
    deleted_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     db_table = 'mb_user_deletions'

class WmsDeletion(models.Model):
    wms_id = models.IntegerField()
    wms_title = models.CharField(max_length=255)
    contactelectronicmailaddress = models.CharField(max_length=255)
    deleted_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     db_table = 'wms_deletions'

    # def __str__(self):
    #     return f"{self.wms_title} ({self.contactelectronicmailaddress})"

class WfsDeletion(models.Model):
    wfs_id = models.IntegerField()
    wfs_title = models.CharField(max_length=255)
    deleted_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     db_table = 'wfs_deletions'

class WmcDeletion(models.Model):
    wmc_id = models.IntegerField()
    wmc_title = models.CharField(max_length=255)
    deleted_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
    #     db_table = 'wmc_deletions'

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

class InspireCategory(models.Model):
    fkey_layer_id = models.IntegerField(db_column='fkey_layer_id', primary_key=True)
    fkey_inspire_category_id = models.IntegerField(db_column='fkey_inspire_category_id')
    fkey_metadata_id = models.IntegerField(db_column='fkey_metadata_id')

    class Meta:
        db_table = '"mapbender"."layer_inspire_category"' 
        managed = False  # Disable migrations for this table, as it already exists
        unique_together = ('fkey_layer_id', 'fkey_inspire_category_id', 'fkey_metadata_id')

class InspireCategories_detail(models.Model):
    inspire_category_id = models.IntegerField(db_column='inspire_category_id', primary_key=True)
    inspire_category_code_en=  models.CharField(db_column='inspire_category_code_en', max_length=255)

    class Meta:
        db_table = '"mapbender"."inspire_category"' 
        managed=False
        unique_together = ('inspire_category_id', 'inspire_category_code_en')

class IsoCategory(models.Model):
    fkey_layer_id = models.IntegerField(db_column='fkey_layer_id', primary_key=True)
    fkey_md_topic_category = models.IntegerField(db_column='fkey_md_topic_category_id')

    class Meta:
        db_table = '"mapbender"."layer_md_topic_category"'
        managed = False

class IsoTopicCategory(models.Model):
    md_topic_category_id = models.ForeignKey(IsoCategory, db_column='md_topic_category_id', on_delete=models.CASCADE)
    md_topic_category_code_en = models.CharField(db_column='md_topic_category_code_en', max_length=255)
    md_topic_category_code_de = models.CharField(db_column='md_topic_category_code_de', max_length=255)

    class Meta:
        db_table = '"mapbender"."md_topic_category"'
        managed = False