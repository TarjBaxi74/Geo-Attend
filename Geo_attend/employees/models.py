# models.py
from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    cmp_id = models.CharField(max_length=10, unique=True,null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.name} ({self.cmp_id})"

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=15,null=True, blank=True)
    company = models.ForeignKey(Location, on_delete=models.CASCADE,null=True, related_name='employees',blank=True)

    def __str__(self):
        return f"({self.id})"

class AttendanceRecord(models.Model):
    user = models.ForeignKey(Employee, on_delete=models.CASCADE)
    company = models.ForeignKey(Location, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attendance by {self.user.username} on {self.timestamp}"
class LeaveApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    leave_id = models.PositiveIntegerField(unique=True, blank=True, null=True)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leave_id} | {self.employee.user.username} | {self.start_date} to {self.end_date}"

    def save(self, *args, **kwargs):
        if self.leave_id is None:
            last = LeaveApplication.objects.all().order_by('-leave_id').first()
            self.leave_id = 1 if not last else last.leave_id + 1
        super().save(*args, **kwargs)
