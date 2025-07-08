# from django import template
# from ..models import AttendanceRecord, StudentAttendance

# register = template.Library()

# @register.filter
# def get_week(queryset, week):
#     """Get attendance record for specific week"""
#     try:
#         week_num = int(week)
#         return queryset.filter(week_number=week_num).first()
#     except (ValueError, AttributeError):
#         return None

# @register.filter
# def count_present(record):
#     """Count present students for a record"""
#     if not record:
#         return 0
#     return record.student_attendances.filter(is_present=True).count()

# @register.filter
# def get_student_attendance(record, student_id):
#     """Get student's attendance status"""
#     if not record:
#         return {'is_present': False, 'remarks': ''}
#     try:
#         return record.student_attendances.get(student_id=student_id)
#     except StudentAttendance.DoesNotExist:
#         return {'is_present': False, 'remarks': ''}

# @register.filter
# def has_signed_current_week(enrollment, args):
#     """Check if student has signed for current week"""
#     try:
#         current_week, unit_id = args.split(',')
#         return AttendanceRecord.objects.filter(
#             unit_allocation_id=unit_id,
#             week_number=int(current_week),
#             student_attendances__student_id=enrollment.student_id
#         ).exists()
#     except:
#         return False

# @register.filter
# def multiply(value, arg):
#     """Multiply two values"""
#     try:
#         return float(value) * float(arg)
#     except:
#         return 0