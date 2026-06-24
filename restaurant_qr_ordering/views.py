from django.shortcuts import render


def home_view(request):
    """Home page - main entry point for the QR-Based Food Ordering System."""
    return render(request, 'home.html')
