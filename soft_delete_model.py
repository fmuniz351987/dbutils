from django.db import models
from django.utils import timezone


class SoftDeletionQuerySet(models.QuerySet):
	def delete(self):
		return super(SoftDeletionQuerySet, self).update(deleted_at=timezone.now())

	def hard_delete(self):
		return super(SoftDeletionQuerySet, self).delete()

	def alive(self):
		return self.filter(deleted_at=None)

	def dead(self):
		return self.exclude(deleted_at=None)


class SoftDeletionManager(models.Manager):
	def __init__(self, *args, **kwargs):
		self.alive_only = kwargs.pop('alive_only', True)
		super(SoftDeletionManager, self).__init__(*args, **kwargs)

	def get_queryset(self):
		if self.alive_only:
			return SoftDeletionQuerySet(self.model).filter(deleted_at=None)
		return SoftDeletionQuerySet(self.model)

	def hard_delete(self):
		return self.get_queryset().hard_delete()


class SoftDeleteModel(models.Model):

	class Meta:
		abstract = True
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	deleted_at = models.DateTimeField(default=None, null=True, blank=True, editable=False)

	objects = SoftDeletionManager()
	all_objects = SoftDeletionManager(alive_only=False)
	
	def delete(self):
		self.deleted_at = timezone.now()
		self.save()

	def hard_delete(self):
		super(SoftDeletionManager, self).delete()
