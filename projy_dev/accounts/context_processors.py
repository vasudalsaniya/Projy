def user_notifications(request):
    if request.user.is_authenticated:
        # Fetch unread notifications for the logged-in user
        unread = request.user.notifications.filter(is_read=False)
        return {'unread_notifications': unread, 'unread_count': unread.count()}
    return {}