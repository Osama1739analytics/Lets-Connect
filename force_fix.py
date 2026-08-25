import sys
file_path = r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\home\views.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We know the mangled mess starts around delete_session and stops around chat_inbox
start_marker = "    if request.method == 'POST':\n        session.delete()\n        messages.success(request, 'Session deleted successfully.')\n"
end_marker = "    from .models import DirectMessage\n\n    # Get distinct users the current user has chatted with\n"

if start_marker in content and end_marker in content:
    start_idx = content.find(start_marker) + len(start_marker)
    end_idx = content.find(end_marker)
    
    new_content = content[:start_idx] + """        return redirect('home:browse_sessions')
        
    return redirect('home:browse_sessions')

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    from .models import Notification
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('home:notifications')

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('home:notifications')

@login_required
def update_presence(request):
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(User.PRESENCE_STATUS_CHOICES):
            request.user.presence_status = status
            request.user.save()
            messages.success(request, f"Status updated to {status.capitalize()}.")
    return redirect(request.META.get('HTTP_REFERER', 'home:index'))

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('/profile/')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'edit_profile.html', {
        'form': form,
        'user': request.user
    })

@login_required
def chat_inbox(request):
    \"\"\"View to list all active conversations.\"\"\"
    from django.db.models import Q, Max
""" + content[end_idx:]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Fixed home/views.py")
else:
    print("Markers not found!")
    if start_marker not in content:
        print("Start marker not found")
    if end_marker not in content:
        print("End marker not found")
