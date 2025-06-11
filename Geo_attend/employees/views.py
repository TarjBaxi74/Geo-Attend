from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
import datetime
import json
from django.core.mail import send_mail
from .models import Employee, Location, AttendanceRecord, LeaveApplication
from .utils import is_within_geofence, calculate_leave_days, auto_approve_leave
import hmac
import hashlib
import base64
import time
import qrcode
from django.http import HttpResponse
from io import BytesIO
SECRET_KEY = b'megha'

def generate_qr_code(request, cmp_id):
    timestamp = int(time.time())
    payload = f"{cmp_id}:{timestamp}"
    signature = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    qr_data = {
        "cmp_id": cmp_id,
        "timestamp": timestamp,
        "token": signature
    }

    qr = qrcode.make(json.dumps(qr_data))
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")
# Utility to generate unique company ID
def generate_cmp_id():
    last_company = Location.objects.order_by('-id').first()
    next_id = 1 if not last_company else last_company.id + 1
    return f"CMP{next_id:04d}"


@csrf_exempt
def cmp_admin(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")
        company_code = data.get("cmp_id")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if Location.objects.filter(cmp_id=company_code).exists():
                login(request, user)
                return JsonResponse({"status": "success", "message": "Logged in"})
            else:
                return JsonResponse({"status": "error", "message": "Invalid company code"}, status=400)
        else:
            return JsonResponse({"status": "error", "message": "Invalid email or password"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        data = json.loads(request.body)
        email = data["username"]
        password = data["password"]

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"status": "success", "message": "Logged in"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid credentials"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    logout(request)
    return JsonResponse({"status": "success", "message": "Logged out"})


@csrf_exempt
@require_http_methods(["POST"])
def register_company(request):
    try:
        data = json.loads(request.body)
        name, email = data["name"], data["email"]
        lat, lng = data["lat"], data["lng"]
        radius = data.get("radius", 100)

        if Location.objects.filter(name=name).exists():
            return JsonResponse({"status": "error", "message": "Company already exists"}, status=400)

        cmp_id = generate_cmp_id()
        company = Location.objects.create(cmp_id=cmp_id, name=name, email=email, latitude=lat, longitude=lng, radius=radius)

        return JsonResponse({"status": "success", "company_id": company.id, "cmp_id": cmp_id})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def mark_attendance(request):
    try:
        data = json.loads(request.body)
        lat = data.get("lat")
        lng = data.get("lng")
        username = data.get("username")

        if not username or lat is None or lng is None:
            return JsonResponse({"status": "error", "message": "Missing required fields"}, status=400)

        lat = float(lat)
        lng = float(lng)
        user = get_object_or_404(User, username=username)
        employee = get_object_or_404(Employee, user=user)
        company = employee.company

        if not company:
            return JsonResponse({"status": "error", "message": "Company location not assigned"}, status=400)

        if is_within_geofence((lat, lng), company):
            AttendanceRecord.objects.create(
                user=employee,
                company=company,
                latitude=lat,
                longitude=lng,
                timestamp=datetime.datetime.now()
            )
            send_mail(
            subject="Attendance Marked",
            message=f"Hi {user.first_name}, your attendance was successfully marked on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
            from_email="emailjs15@gmail.com",
            recipient_list=[user.email],
            fail_silently=False,
            )
        
            return JsonResponse({"status": "success", "message": "Attendance marked"})
        else:
            return JsonResponse({"status": "failed", "message": "Outside your company location zone"})

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def get_all_attendance_records(request):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        user = get_object_or_404(User, username=username)
        employee = get_object_or_404(Employee, user=user)

        records = AttendanceRecord.objects.filter(user=employee).select_related("user", "company")
        result = [{
            "date": record.timestamp.date().isoformat(),
            "time_in": record.timestamp.time().isoformat(),
            "time_out": None,
            "location": f"{record.latitude}, {record.longitude}"
        } for record in records]

        return JsonResponse({"status": "success", "records": result}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def create_employee(request):
    try:
        data = json.loads(request.body)
        username = data["username"]
        password = data["password"]
        first_name = data["first_name"]
        last_name = data["last_name"]
        email = data["email"]
        phone = data["phone"]
        company_name = data["company"]

        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": "error", "message": "User already exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"status": "error", "message": "Email already used"}, status=400)

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        company = get_object_or_404(Location, name=company_name)
        employee = Employee.objects.create(user=user, phone=phone, company=company)

        return JsonResponse({
            "status": "success",
            "user_id": user.id,
            "employee_id": employee.id
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def get_employee(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "unauthenticated"}, status=401)
    try:
        employee = get_object_or_404(Employee, user=request.user)
        user = employee.user

        data = {
            "id": employee.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": employee.phone,
            "company": {
                "name": employee.company.name,
                "latitude": employee.company.latitude,
                "longitude": employee.company.longitude
            } if employee.company else None
        }

        return JsonResponse({"status": "success", "employee": data})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT"])
@login_required
def update_employee(request, employee_id):
    try:
        data = json.loads(request.body)
        employee = get_object_or_404(Employee, id=employee_id)
        user = employee.user

        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.email = data.get("email", user.email)
        if data.get("password"):
            user.password = make_password(data["password"])
        user.save()

        employee.phone = data.get("phone", employee.phone)
        employee.save()

        return JsonResponse({"status": "success", "message": "Employee updated"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_employee(request, employee_id):
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        user = employee.user
        user.delete()
        return JsonResponse({"status": "success", "message": "Employee deleted"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
def get_logged_in_employee(request):
    try:
        employee = Employee.objects.get(user=request.user)
        return JsonResponse({
            "employee_id": employee.id,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "phone": employee.phone,
        })
    except Employee.DoesNotExist:
        return JsonResponse({"error": "Employee not found"}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def apply_leave(request):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        reason = data.get("reason", "")

        if not username or not start_date or not end_date:
            return JsonResponse({"status": "error", "message": "Username, start_date, and end_date are required."}, status=400)

        user = get_object_or_404(User, username=username)
        employee = get_object_or_404(Employee, user=user)

        total_days = calculate_leave_days(start_date, end_date)
        leave_status = "Approved" if auto_approve_leave(total_days) else "Pending"

        leave = LeaveApplication.objects.create(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            status=leave_status
        )

        return JsonResponse({
            "leave_id": leave.leave_id,
            "employee_username": employee.user.username,
            "start_date": str(leave.start_date),
            "end_date": str(leave.end_date),
            "total_days": leave.total_days,
            "reason": leave.reason,
            "status": leave.status,
            "created_at": leave.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }, status=201)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
@csrf_exempt
@require_http_methods(["POST"])
def mark_attendance_via_qr(request):
    try:
        data = json.loads(request.body)
        cmp_id = data["cmp_id"]
        timestamp = int(data["timestamp"])
        token = data["token"]
        username = data["username"]
        lat = float(data["lat"])
        lng = float(data["lng"])

        # 1. Verify timestamp freshness (5 mins max)
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:
            return JsonResponse({"status": "error", "message": "QR expired"})

        # 2. Verify token validity
        payload = f"{cmp_id}:{timestamp}"
        expected_token = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(token, expected_token):
            return JsonResponse({"status": "error", "message": "Invalid QR token"})

        # 3. Verify location
        company = get_object_or_404(Location, cmp_id=cmp_id)
        if not is_within_geofence((lat, lng), company):
            return JsonResponse({"status": "error", "message": "Outside geofence"})

        # 4. Mark attendance
        user = get_object_or_404(User, username=username)
        employee = get_object_or_404(Employee, user=user)
        AttendanceRecord.objects.create(
            user=employee,
            company=company,
            latitude=lat,
            longitude=lng,
            timestamp=datetime.datetime.now()
        )

        return JsonResponse({"status": "success", "message": "Attendance marked"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
