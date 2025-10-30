from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CandidateRegisterForm, RecruiterRegisterForm, CandidateProfileForm
from .models import CandidateDocument, RecruiterDocument
from datetime import datetime
from bson import ObjectId  # ✅ pour valider les ObjectId MongoDB


# ==================== HOME ====================
def home(request):
    """Page d'accueil"""
    return render(request, 'accounts/home.html')


# ==================== REGISTER ====================
def register_choice(request):
    """Choix du type de compte"""
    return render(request, 'accounts/register_choice.html')

def register_candidate(request):
    """Inscription Candidat"""
    if request.method == 'POST':
        form = CandidateRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Vérifier si le document existe déjà
            try:
                candidate_doc = CandidateDocument.objects.get(user_id=user.id)
            except CandidateDocument.DoesNotExist:
                candidate_doc = CandidateDocument(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email
                )
                candidate_doc.save()

            # Associer le mongo_id au compte Django
            user.mongo_id = str(candidate_doc.id)
            user.role = "candidate"
            user.save()

            login(request, user)
            messages.success(request, 'Inscription réussie ! Bienvenue sur la plateforme.')
            return redirect('dashboard_redirect')
    else:
        form = CandidateRegisterForm()
    
    return render(request, 'accounts/register_candidate.html', {'form': form})

def register_recruiter(request):
    if request.method == 'POST':
        form = RecruiterRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # ✅ Le form.save() s'occupe de tout
            
            login(request, user)
            messages.success(request, 'Inscription réussie !')
            return redirect('dashboard_redirect')
    else:
        form = RecruiterRegisterForm()
    
    return render(request, 'accounts/register_recruiter.html', {'form': form})


# ==================== DASHBOARDS ====================
@login_required
def candidate_dashboard(request):
    """Dashboard Candidat"""
    mongo_id = getattr(request.user, "mongo_id", None)

    # ✅ Vérifie si l'ID est vide ou invalide
    if not mongo_id or not ObjectId.is_valid(mongo_id):
        messages.error(request, "Accès refusé : identifiant Mongo invalide ou manquant.")
        return redirect('home')

    try:
        candidate = CandidateDocument.objects.get(id=mongo_id)
    except CandidateDocument.DoesNotExist:
        messages.error(request, "Accès refusé. Document candidat introuvable.")
        return redirect('home')

    return render(request, 'accounts/dashboard_candidate.html', {'candidate': candidate})


@login_required
def recruiter_dashboard(request):
    """Dashboard Recruteur"""
    mongo_id = getattr(request.user, "mongo_id", None)

    if not mongo_id or not ObjectId.is_valid(mongo_id):
        messages.error(request, "Accès refusé : identifiant Mongo invalide ou manquant.")
        return redirect('home')

    try:
        recruiter = RecruiterDocument.objects.get(id=mongo_id)
    except RecruiterDocument.DoesNotExist:
        messages.error(request, "Accès refusé. Document recruteur introuvable.")
        return redirect('home')

    return render(request, 'accounts/dashboard_recruiter.html', {'recruiter': recruiter})


# ✅ Redirection automatique selon le rôle utilisateur
@login_required
def dashboard_redirect(request):
    """Redirige automatiquement vers le bon tableau de bord selon le rôle."""
    user = request.user

    if user.role == 'candidate':
        return redirect('candidate_dashboard')
    elif user.role == 'recruiter':
        return redirect('recruiter_dashboard')
    else:
        messages.warning(request, "Aucun rôle associé à ce compte.")
        return redirect('home')


# ==================== PROFILES ====================
@login_required
def candidate_profile(request):
    """Profil Candidat"""
    mongo_id = getattr(request.user, "mongo_id", None)

    if not mongo_id or not ObjectId.is_valid(mongo_id):
        messages.error(request, "Profil invalide : identifiant Mongo manquant.")
        return redirect('home')

    try:
        candidate = CandidateDocument.objects.get(id=mongo_id)
    except CandidateDocument.DoesNotExist:
        messages.error(request, "Document candidat introuvable.")
        return redirect('home')

    if request.method == 'POST':
        form = CandidateProfileForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            candidate.first_name = data['first_name']
            candidate.last_name = data['last_name']
            candidate.phone = data['phone']
            candidate.location = data['location']
            candidate.experience_years = data['experience_years']
            candidate.desired_position = data['desired_position']
            candidate.desired_salary = data['desired_salary']
            candidate.updated_at = datetime.now()
            candidate.save()
            messages.success(request, 'Profil mis à jour avec succès !')
            return redirect('candidate_profile')
    else:
        initial = {
            'first_name': candidate.first_name,
            'last_name': candidate.last_name,
            'phone': candidate.phone,
            'location': candidate.location,
            'experience_years': getattr(candidate, 'experience_years', 0),
            'desired_position': getattr(candidate, 'desired_position', ''),
            'desired_salary': getattr(candidate, 'desired_salary', 0),
        }
        form = CandidateProfileForm(initial=initial)

    return render(request, 'accounts/profile_candidate.html', {
        'form': form,
        'candidate': candidate
    })


@login_required
def recruiter_profile(request):
    """Profil Recruteur"""
    mongo_id = getattr(request.user, "mongo_id", None)

    if not mongo_id or not ObjectId.is_valid(mongo_id):
        messages.error(request, "Profil invalide : identifiant Mongo manquant.")
        return redirect('home')

    try:
        recruiter = RecruiterDocument.objects.get(id=mongo_id)
    except RecruiterDocument.DoesNotExist:
        messages.error(request, "Document recruteur introuvable.")
        return redirect('home')
    
    if request.method == 'POST':
        data = request.POST
        recruiter.first_name = data.get('first_name', recruiter.first_name)
        recruiter.last_name = data.get('last_name', recruiter.last_name)
        recruiter.phone = data.get('phone', recruiter.phone)
        recruiter.position = data.get('position', recruiter.position)
        recruiter.updated_at = datetime.now()
        recruiter.save()
        messages.success(request, 'Profil mis à jour avec succès !')
        return redirect('recruiter_profile')
    
    initial = {
        'first_name': recruiter.first_name,
        'last_name': recruiter.last_name,
        'phone': recruiter.phone,
        'position': getattr(recruiter, 'position', ''),
    }

    return render(request, 'accounts/profile_recruiter.html', {
        'recruiter': recruiter,
    })


@login_required
def logout_view(request):
    """Déconnexion sécurisée"""
    # Déconnecte l'utilisateur
    logout(request)
    
    # Supprime complètement la session
    request.session.flush()
    
    # Supprime le cookie de session côté navigateur
    response = redirect('login')
    response.delete_cookie('sessionid')
    
    messages.info(request, 'Vous avez été déconnecté.')
    return response