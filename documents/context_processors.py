from .models import Notification

def notifications(request):
    """Add unread notifications count to context"""
    if request.user.is_authenticated:
        unread = Notification.objects.filter(user=request.user, is_read=False)
        return {
            'notifications': unread,
            'unread_count': unread.count()
        }
    return {
        'notifications': [],
        'unread_count': 0
    }