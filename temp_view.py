
@login_required
def edit_profile(request):
    """View for users to edit their profile information"""
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
