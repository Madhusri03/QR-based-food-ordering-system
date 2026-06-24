from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        # Redirect based on role if already logged in
        if hasattr(request.user, 'profile'):
            if request.user.profile.role == 'ADMIN':
                return redirect('admin_panel:dashboard')
            elif request.user.profile.role == 'KITCHEN':
                return redirect('kitchen:dashboard')
        return redirect('/')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                
                # Check user role and redirect
                if hasattr(user, 'profile'):
                    if user.profile.role == 'ADMIN':
                        return redirect('admin_panel:dashboard')
                    elif user.profile.role == 'KITCHEN':
                        return redirect('kitchen:dashboard')
                
                return redirect('/')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('accounts:login')
