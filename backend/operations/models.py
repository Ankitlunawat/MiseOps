from django.db import models
from django.db.models import Q

class WorkOrder(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        PREPARING = 'preparing', 'Preparing'
        READY = 'ready', 'Ready'
        CLOSED = 'closed', 'Closed'
    title = models.CharField(max_length=120)
    station = models.CharField(max_length=60)
    assignee = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField()
    due = models.DateTimeField()
    priority = models.CharField(max_length=10, choices=[('normal', 'Normal'), ('urgent', 'Urgent')], default='normal')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    notes = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['due', 'id']
        constraints = [models.CheckConstraint(condition=Q(quantity__gte=1), name='positive_work_quantity')]

class Activity(models.Model):
    order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='activity')
    actor = models.CharField(max_length=150)
    message = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at', 'id']
