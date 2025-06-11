import math
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
def is_within_geofence(user_coords, location):
    """
    user_coords: (lat, lon) in degrees
    location: a Location instance with .latitude, .longitude, .radius (in kilometers)
    """

    # Convert degrees to radians
    lat1 = math.radians(location.latitude)
    lon1 = math.radians(location.longitude)
    lat2 = math.radians(user_coords[0])
    lon2 = math.radians(user_coords[1])
 
    # Earth's radius in kilometers
    R = 6371

    # Spherical Law of Cosines
    #Haversine Formula
    distance = R * math.acos(
        math.sin(lat1) * math.sin(lat2) +
        math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    )

    print("Distance in km:", distance)
    return distance <= location.radius


def calculate_leave_days(start, end):
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    if start_date > end_date:
        raise ValidationError("Start date cannot be after end date.")
    return (end_date - start_date).days + 1

def auto_approve_leave( requested_days):
    
    if requested_days <= 2:
        return True
    return False

def send_leave_notification(employee, status, reason=None):
    """
    Send email or dashboard notification to employee and admin.
    (Stub for integration)
    """
    print(f"[Notification] {employee.name}'s leave {status}.")
    if reason:
        print(f"Reason: {reason}")
