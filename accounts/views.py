from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CandidateRegisterForm, RecruiterRegisterForm, CandidateProfileForm
from .models import CandidateDocument, RecruiterDocument, CompanyDocument
from datetime import datetime
from bson import ObjectId  # ✅ pour valider les ObjectId MongoDB
from jobs.models import JobDocument, ApplicationDocument
from jobs.views import calculate_match_score

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
    """Dashboard candidat avec données réelles"""
    if request.user.role != 'candidate':
        return redirect('recruiter_dashboard')
    
    try:
        candidate = CandidateDocument.objects.get(id=request.user.mongo_id)
        
        # ==================== STATISTIQUES RÉELLES ====================
        
        # Nombre de candidatures
        applications = ApplicationDocument.objects.filter(candidate_id=candidate.id)
        total_applications = applications.count()
        
        # Candidatures par statut
        pending_applications = applications.filter(status='SUBMITTED').count()
        viewed_applications = applications.filter(status='VIEWED').count()
        shortlisted_applications = applications.filter(status='SHORTLISTED').count()
        interview_applications = applications.filter(status='INTERVIEW').count()
        
        # Score moyen de matching
        scores = [app.ai_match_score for app in applications if app.ai_match_score]
        avg_match_score = round(sum(scores) / len(scores)) if scores else 0
        
        # Profil complété
        profile_completion = calculate_profile_completion(candidate)
        
        # ==================== CANDIDATURES RÉCENTES ====================
        recent_applications = applications.order_by('-applied_at')[:5]
        
        # Enrichir avec les données des offres
        applications_data = []
        for app in recent_applications:
            try:
                job = JobDocument.objects.get(id=app.job_id)
                applications_data.append({
                    'application': app,
                    'job': job,
                    'days_ago': (datetime.now() - app.applied_at).days
                })
            except JobDocument.DoesNotExist:
                pass
        
        # ==================== OFFRES RECOMMANDÉES ====================
        # Top 5 offres avec meilleur matching
        all_jobs = JobDocument.objects.filter(status='PUBLISHED')
        
        # Exclure les offres déjà postulées
        applied_job_ids = [app.job_id for app in applications]
        available_jobs = [job for job in all_jobs if job.id not in applied_job_ids]
        
        # Calculer les scores et trier
        recommended_jobs = []
        for job in available_jobs[:20]:  # Limiter pour performance
            score = calculate_match_score(candidate, job)
            if score >= 50:  # Minimum 50% de matching
                recommended_jobs.append({
                    'job': job,
                    'match_score': score
                })
        
        # Trier par score décroissant
        recommended_jobs = sorted(recommended_jobs, key=lambda x: x['match_score'], reverse=True)[:5]
        
        # ==================== STATISTIQUES PROFIL ====================
        # Vues du profil (à implémenter plus tard avec un modèle ProfileView)
        profile_views = 0  # TODO: Implémenter tracking
        
        context = {
            'candidate': candidate,
            'stats': {
                'total_applications': total_applications,
                'pending': pending_applications,
                'viewed': viewed_applications,
                'shortlisted': shortlisted_applications,
                'interviews': interview_applications,
                'avg_match_score': avg_match_score,
                'profile_completion': profile_completion,
                'profile_views': profile_views,
            },
            'recent_applications': applications_data,
            'recommended_jobs': recommended_jobs,
        }
        
        return render(request, 'accounts/dashboard_candidate.html', context)
        
    except CandidateDocument.DoesNotExist:
        messages.error(request, "Profil candidat introuvable.")
        return redirect('home')


@login_required
def recruiter_dashboard(request):
    """Dashboard recruteur avec données réelles"""
    if request.user.role != 'recruiter':
        return redirect('candidate_dashboard')
    
    try:
        recruiter = RecruiterDocument.objects.get(id=request.user.mongo_id)
        company = CompanyDocument.objects.get(id=recruiter.company_id)
        
        # ==================== STATISTIQUES RÉELLES ====================
        
        # Offres de l'entreprise
        jobs = JobDocument.objects.filter(company_id=company.id)
        total_jobs = jobs.count()
        active_jobs = jobs.filter(status='PUBLISHED').count()
        
        # Toutes les candidatures pour les offres de l'entreprise
        job_ids = [job.id for job in jobs]
        applications = ApplicationDocument.objects.filter(job_id__in=job_ids)
        
        total_applications = applications.count()
        new_applications = applications.filter(status='SUBMITTED').count()
        shortlisted = applications.filter(status='SHORTLISTED').count()
        
        # Vues totales (somme des vues de toutes les offres)
        total_views = sum(job.views_count for job in jobs)
        
        # ==================== OFFRES ACTIVES AVEC STATS ====================
        active_jobs_data = []
        for job in jobs.filter(status='PUBLISHED').order_by('-published_at')[:5]:
            job_applications = applications.filter(job_id=job.id)
            
            active_jobs_data.append({
                'job': job,
                'applications_count': job_applications.count(),
                'new_applications': job_applications.filter(status='SUBMITTED').count(),
                'shortlisted': job_applications.filter(status='SHORTLISTED').count(),
                'views': job.views_count,
                'days_ago': (datetime.now() - job.published_at).days if job.published_at else 0
            })
        
        # ==================== CANDIDATURES RÉCENTES ====================
        recent_applications = applications.order_by('-applied_at')[:8]
        
        # Enrichir avec données candidat et job
        applications_data = []
        for app in recent_applications:
            try:
                candidate = CandidateDocument.objects.get(id=app.candidate_id)
                job = JobDocument.objects.get(id=app.job_id)
                
                applications_data.append({
                    'application': app,
                    'candidate': candidate,
                    'job': job,
                    'hours_ago': int((datetime.now() - app.applied_at).total_seconds() / 3600)
                })
            except (CandidateDocument.DoesNotExist, JobDocument.DoesNotExist):
                pass
        
        # ==================== TOP CANDIDATS ====================
        # Meilleurs scores de matching
        top_candidates = applications.filter(
            status__in=['SUBMITTED', 'VIEWED', 'SHORTLISTED']
        ).order_by('-ai_match_score')[:5]
        
        top_candidates_data = []
        for app in top_candidates:
            try:
                candidate = CandidateDocument.objects.get(id=app.candidate_id)
                job = JobDocument.objects.get(id=app.job_id)
                
                top_candidates_data.append({
                    'application': app,
                    'candidate': candidate,
                    'job': job,
                })
            except (CandidateDocument.DoesNotExist, JobDocument.DoesNotExist):
                pass
        
        # ==================== INSIGHTS IA ====================
        # Statistiques intelligentes
        if total_applications > 0:
            avg_match_score = round(sum(app.ai_match_score for app in applications if app.ai_match_score) / total_applications)
            conversion_rate = round((shortlisted / total_applications) * 100) if total_applications > 0 else 0
        else:
            avg_match_score = 0
            conversion_rate = 0
        
        context = {
            'recruiter': recruiter,
            'company': company,
            'stats': {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'total_applications': total_applications,
                'new_applications': new_applications,
                'shortlisted': shortlisted,
                'total_views': total_views,
                'avg_match_score': avg_match_score,
                'conversion_rate': conversion_rate,
            },
            'active_jobs': active_jobs_data,
            'recent_applications': applications_data,
            'top_candidates': top_candidates_data,
        }
        
        return render(request, 'accounts/dashboard_recruiter.html', context)
        
    except (RecruiterDocument.DoesNotExist, CompanyDocument.DoesNotExist):
        messages.error(request, "Profil recruteur introuvable.")
        return redirect('home')


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
    """Profil recruteur"""
    if request.user.role != 'recruiter':
        return redirect('candidate_profile')
    
    mongo_id = getattr(request.user, "mongo_id", None)
    
    if not mongo_id or not ObjectId.is_valid(mongo_id):
        messages.error(request, "Profil invalide : identifiant Mongo manquant.")
        return redirect('home')
    
    try:
        recruiter = RecruiterDocument.objects.get(id=mongo_id)
        company = CompanyDocument.objects.get(id=recruiter.company_id)
        
        if request.method == 'POST':
            # Mise à jour du profil recruteur
            recruiter.first_name = request.POST.get('first_name', recruiter.first_name)
            recruiter.last_name = request.POST.get('last_name', recruiter.last_name)
            recruiter.phone = request.POST.get('phone', recruiter.phone)
            recruiter.position = request.POST.get('position', recruiter.position)
            recruiter.updated_at = datetime.now()
            recruiter.save()
            
            # Mise à jour de l'entreprise
            company.name = request.POST.get('company_name', company.name)
            company.industry = request.POST.get('industry', company.industry)
            company.size = request.POST.get('size', company.size)
            company.website = request.POST.get('website', company.website)
            company.description = request.POST.get('description', company.description)
            company.updated_at = datetime.now()
            company.save()
            
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('recruiter_profile')
        
        context = {
            'recruiter': recruiter,
            'company': company,
        }
        
        return render(request, 'accounts/profile_recruiter.html', context)
        
    except (RecruiterDocument.DoesNotExist, CompanyDocument.DoesNotExist):
        messages.error(request, "Profil recruteur introuvable.")
        return redirect('home')


# ==================== HELPER FUNCTIONS ====================
def calculate_profile_completion(candidate):
    """Calcule le pourcentage de complétion du profil - Version sécurisée"""
    
    # Liste des champs à vérifier (seulement ceux qui existent)
    fields_to_check = [
        'first_name',
        'last_name', 
        'email',
        'phone',
        'location',
        'cv_url',
        'skills',
        'education',
        'experience',
        'experience_years',
        'desired_position',
        'desired_salary',
    ]
    
    completed = 0
    total = 0
    
    for field_name in fields_to_check:
        # Vérifier si le champ existe
        if hasattr(candidate, field_name):
            total += 1
            value = getattr(candidate, field_name, None)
            
            # Vérifier si le champ est rempli
            if isinstance(value, list):
                if value and len(value) > 0:
                    completed += 1
            elif isinstance(value, (int, float)):
                if value and value > 0:
                    completed += 1
            elif value:  # string, bool, etc.
                completed += 1
    
    return round((completed / total) * 100) if total > 0 else 0


# ==================== LOGOUT ====================
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