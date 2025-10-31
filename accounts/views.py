from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CandidateRegisterForm, RecruiterRegisterForm, CandidateProfileForm
from .models import CandidateDocument, RecruiterDocument, CompanyDocument
from datetime import datetime
from bson import ObjectId
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

            # Vérifier si un document existe déjà (utiliser first() au lieu de get())
            candidate_doc = CandidateDocument.objects.filter(user_id=user.id).first()
            
            if not candidate_doc:
                # Créer le document seulement s'il n'existe pas
                candidate_doc = CandidateDocument(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
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
            user = form.save()
            
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
    
    # ==================== VÉRIFICATION ET CORRECTION DU MONGO_ID ====================
    if not request.user.mongo_id or request.user.mongo_id == 'None':
        messages.warning(request, "Configuration de votre profil en cours...")
        
        try:
            candidate = CandidateDocument.objects.get(user_id=request.user.id)
        except CandidateDocument.DoesNotExist:
            candidate = CandidateDocument(
                user_id=request.user.id,
                username=request.user.username,
                first_name=request.user.first_name or 'Candidat',
                last_name=request.user.last_name or 'Test',
                email=request.user.email,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            candidate.save()
        
        request.user.mongo_id = str(candidate.id)
        request.user.save()
        
        messages.success(request, "Profil configuré avec succès !")
    
    try:
        candidate = CandidateDocument.objects.get(id=request.user.mongo_id)
        
        # ==================== STATISTIQUES RÉELLES ====================
        applications = ApplicationDocument.objects.filter(candidate_id=candidate.id)
        total_applications = applications.count()
        
        pending_applications = applications.filter(status='SUBMITTED').count()
        viewed_applications = applications.filter(status='VIEWED').count()
        shortlisted_applications = applications.filter(status='SHORTLISTED').count()
        interview_applications = applications.filter(status='INTERVIEW').count()
        
        scores = [app.ai_match_score for app in applications if app.ai_match_score]
        avg_match_score = round(sum(scores) / len(scores)) if scores else 0
        
        profile_completion = calculate_profile_completion(candidate)
        
        # ==================== CANDIDATURES RÉCENTES ====================
        recent_applications = applications.order_by('-applied_at')[:5]
        
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
        all_jobs = JobDocument.objects.filter(status='PUBLISHED')
        
        applied_job_ids = [app.job_id for app in applications]
        available_jobs = [job for job in all_jobs if job.id not in applied_job_ids]
        
        recommended_jobs = []
        for job in available_jobs[:20]:
            score = calculate_match_score(candidate, job)
            if score >= 50:
                recommended_jobs.append({
                    'job': job,
                    'match_score': score
                })
        
        recommended_jobs = sorted(recommended_jobs, key=lambda x: x['match_score'], reverse=True)[:5]
        
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
                'profile_views': 0,
            },
            'recent_applications': applications_data,
            'recommended_jobs': recommended_jobs,
        }
        
        return render(request, 'accounts/dashboard_candidate.html', context)
        
    except CandidateDocument.DoesNotExist:
        messages.error(request, "Erreur lors du chargement de votre profil.")
        return redirect('logout')


@login_required
def recruiter_dashboard(request):
    """Dashboard recruteur avec données réelles"""
    if request.user.role != 'recruiter':
        return redirect('candidate_dashboard')
    
    # ==================== VÉRIFICATION ET CORRECTION DU MONGO_ID ====================
    if not request.user.mongo_id or request.user.mongo_id == 'None':
        messages.warning(request, "Configuration de votre profil en cours...")
        
        try:
            recruiter = RecruiterDocument.objects.get(user_id=request.user.id)
        except RecruiterDocument.DoesNotExist:
            company = CompanyDocument(
                name=f"Entreprise de {request.user.username}",
                industry="Non spécifié",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            company.save()
            
            recruiter = RecruiterDocument(
                user_id=request.user.id,
                username=request.user.username,
                first_name=request.user.first_name or 'Recruteur',
                last_name=request.user.last_name or 'Test',
                email=request.user.email,
                position="Recruteur",
                company_id=str(company.id),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            recruiter.save()
        
        request.user.mongo_id = str(recruiter.id)
        request.user.save()
        
        messages.success(request, "Profil configuré avec succès !")
    
    try:
        recruiter = RecruiterDocument.objects.get(id=request.user.mongo_id)
        company = CompanyDocument.objects.get(id=recruiter.company_id)
        
        jobs = JobDocument.objects.filter(company_id=company.id)
        total_jobs = jobs.count()
        active_jobs = jobs.filter(status='PUBLISHED').count()
        
        job_ids = [job.id for job in jobs]
        applications = ApplicationDocument.objects.filter(job_id__in=job_ids)
        
        total_applications = applications.count()
        new_applications = applications.filter(status='SUBMITTED').count()
        shortlisted = applications.filter(status='SHORTLISTED').count()
        
        total_views = sum(job.views_count for job in jobs)
        
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
        
        recent_applications = applications.order_by('-applied_at')[:8]
        
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
        
        if total_applications > 0:
            avg_match_score = round(sum(app.ai_match_score for app in applications if app.ai_match_score) / total_applications)
            conversion_rate = round((shortlisted / total_applications) * 100)
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
    """Profil Candidat - Formulaire complet"""
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
        candidate.first_name = request.POST.get('first_name', candidate.first_name)
        candidate.last_name = request.POST.get('last_name', candidate.last_name)
        candidate.phone = request.POST.get('phone', '')
        candidate.location = request.POST.get('location', '')
        candidate.experience_years = int(request.POST.get('experience_years', 0))
        
        skills_input = request.POST.get('skills', '')
        if skills_input:
            candidate.skills = [s.strip() for s in skills_input.split(',') if s.strip()]
        
        experiences = []
        exp_index = 0
        while f'exp_title_{exp_index}' in request.POST:
            title = request.POST.get(f'exp_title_{exp_index}', '').strip()
            company = request.POST.get(f'exp_company_{exp_index}', '').strip()
            start_date = request.POST.get(f'exp_start_{exp_index}', '').strip()
            end_date = request.POST.get(f'exp_end_{exp_index}', '').strip()
            description = request.POST.get(f'exp_description_{exp_index}', '').strip()
            
            if title and company:
                experiences.append({
                    'title': title,
                    'company': company,
                    'start_date': start_date,
                    'end_date': end_date,
                    'description': description
                })
            exp_index += 1
        
        candidate.experience = experiences
        
        educations = []
        edu_index = 0
        while f'edu_degree_{edu_index}' in request.POST:
            degree = request.POST.get(f'edu_degree_{edu_index}', '').strip()
            school = request.POST.get(f'edu_school_{edu_index}', '').strip()
            year = request.POST.get(f'edu_year_{edu_index}', '').strip()
            field = request.POST.get(f'edu_field_{edu_index}', '').strip()
            
            if degree and school:
                educations.append({
                    'degree': degree,
                    'school': school,
                    'year': year,
                    'field': field
                })
            edu_index += 1
        
        candidate.education = educations
        
        candidate.desired_position = request.POST.get('desired_position', '')
        candidate.desired_salary = int(request.POST.get('desired_salary', 0)) if request.POST.get('desired_salary') else 0
        
        candidate.updated_at = datetime.now()
        candidate.save()
        
        messages.success(request, 'Profil mis à jour avec succès ! 🎉')
        return redirect('candidate_profile')

    return render(request, 'accounts/profile_candidate.html', {
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
            recruiter.first_name = request.POST.get('first_name', recruiter.first_name)
            recruiter.last_name = request.POST.get('last_name', recruiter.last_name)
            recruiter.phone = request.POST.get('phone', recruiter.phone)
            recruiter.position = request.POST.get('position', recruiter.position)
            recruiter.updated_at = datetime.now()
            recruiter.save()
            
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
    """Calcule le pourcentage de complétion du profil"""
    fields_to_check = [
        'first_name', 'last_name', 'email', 'phone', 'location',
        'cv_url', 'skills', 'education', 'experience',
        'experience_years', 'desired_position', 'desired_salary',
    ]
    
    completed = 0
    total = 0
    
    for field_name in fields_to_check:
        if hasattr(candidate, field_name):
            total += 1
            value = getattr(candidate, field_name, None)
            
            if isinstance(value, list):
                if value and len(value) > 0:
                    completed += 1
            elif isinstance(value, (int, float)):
                if value and value > 0:
                    completed += 1
            elif value:
                completed += 1
    
    return round((completed / total) * 100) if total > 0 else 0


@login_required
def logout_view(request):
    """Déconnexion sécurisée"""
    logout(request)
    request.session.flush()
    
    response = redirect('login')
    response.delete_cookie('sessionid')
    
    messages.info(request, 'Vous avez été déconnecté.')
    return response