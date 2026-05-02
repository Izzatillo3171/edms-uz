from .models import Notification

def notifications(request):
    """Add unread notifications count to context"""
    if request.user.is_authenticated:
        return {
            'notifications': Notification.objects.filter(user=request.user, is_read=False)
        }
    return {'notifications': []}