from django.test import TestCase

from . import models

def lazy_setdefault(d, key, callable):
	if key not in d:
		d[key] = callable()


# Create your tests here.
class CascadeTestCase(TestCase):
	@classmethod
	def create_parent(cls, **kwargs):
		count = models.Parent.objects.count()
		kwargs.setdefault('name', f'Parent#{count}')
		return models.Parent.objects.create(**kwargs)

	@classmethod
	def create_child(cls, **kwargs):
		count = models.Child.objects.count()
		kwargs.setdefault('name', f'Child#{count}')
		lazy_setdefault(kwargs, 'parent', cls.create_parent)
		return models.Child.objects.create(**kwargs)

	def setUp(self):
		self.p1 = self.create_parent()
		self.p2 = self.create_parent()
		self.c1 = self.create_child(parent=self.p1)
		self.c2 = self.create_child(parent=self.p2)

	def test_counts(self):
		self.p2.delete()
		self.assertEqual(models.Parent.objects.count(), 1)
		self.assertEqual(models.Parent.all_objects.count(), 2)

	def test_cascade_hard_delete(self):
		self.p2.hard_delete()
		self.assertEqual(models.Child.objects.count(), 1)

	def test_cascade_soft_delete(self):
		self.p2.delete()
		self.assertEqual(models.Child.objects.count(), 1)
