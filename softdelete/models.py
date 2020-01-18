from django.db import models, transaction
from django.utils import timezone

# Create your models here.
class SoftDeletionQuerySet(models.QuerySet):
	def delete(self):
		with transaction.atomic():
			return super(SoftDeletionQuerySet, self).update(deleted_at=timezone.now())

	def undelete(self):
		return super(SoftDeletionQuerySet, self).update(deleted_at=None)

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
		with transaction.atomic():
			self.deleted_at = timezone.now()
			self.save()
			self.cascade_soft_delete()

	def cascade_soft_delete(self):
		children_filter = {self._meta.model_name: self}
		for field in self._meta.get_fields():
			if field.is_relation and field.on_delete == models.CASCADE:
				field.related_model.objects.filter(**children_filter).delete()

	def hard_delete(self):
		super(SoftDeleteModel, self).delete()

class Parent(SoftDeleteModel):
	name = models.CharField(max_length=64, unique=True)

class Child(SoftDeleteModel):
	name = models.CharField(max_length=64, unique=True)
	parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
