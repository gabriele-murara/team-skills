from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """Soft delete: sets deleted_at. Returns the number of rows."""
        return self.update(deleted_at=timezone.now())

    def force_delete(self):
        return super().delete()

    def restore(self):
        return self.update(deleted_at=None)


class SoftDeleteManager(models.Manager):
    """Default manager: hides the soft deleted rows."""

    def get_queryset(self):
        return self.with_trashed().filter(deleted_at__isnull=True)

    def with_trashed(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_trashed(self):
        return self.with_trashed().filter(deleted_at__isnull=False)


class SoftDeletes(models.Model):
    """
    Soft deletes, as the SoftDeletes trait of Laravel. The model declares
    the deleted_at field (nullable DateTimeField, last field) and extends
    this class before its base model:

        class Product(SoftDeletes, BaseModel):

    delete() sets deleted_at, and objects hides the deleted rows:
    objects.with_trashed() and objects.only_trashed() include them.
    """

    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["deleted_at"])

    def force_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self, using=None):
        self.deleted_at = None
        self.save(using=using, update_fields=["deleted_at"])

    def trashed(self):
        return self.deleted_at is not None
