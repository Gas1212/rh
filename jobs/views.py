from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pymongo import MongoClient
from datetime import datetime, timedelta
from .models import JobDocument
from .forms import JobCreationForm
from .models import JobDocument, ApplicationDocument 
from accounts.models import RecruiterDocument, CompanyDocument, CandidateDocument

def all_jobs(request):
    """
    Vue principale : affiche toutes les offres (externes + internes)
    """
    # Connexion MongoDB pour offres externes
    client = MongoClient(settings.MONGO_URI)
    db_kee = client[settings.MONGO_DATABASE_1][settings.MONGO_COLLECTION]
    db_tanit = client[settings.MONGO_DATABASE_2][settings.MONGO_COLLECTION]
    
    jobs = []
    
    # --- OFFRES KEEJOB (MongoDB) ---
    for job in db_kee.find().limit(100):  # Limiter pour performances
        parsed_job = {
            "id": str(job.get("_id")),
            "source": "Keejob.com",
            "title": job.get("job_title") or job.get("title") or "Titre non disponible",
            "company": job.get("company_name") or job.get("company") or "Entreprise",
            "location": job.get("location") or "Tunisie",
            "description": job.get("description") or job.get("job_description") or "",
            "url_final": job.get("job_url") or job.get("company_url") or "#",
            "logo": job.get("logo"),
            "contract_type": job.get("contract_type"),
            "salary": job.get("salary"),
            "industry": job.get("industry"),
            "parsed_date": parse_date(job.get("date_parsed") or job.get("date")),
            "is_internal": False,
            "is_new": is_new_job(job.get("date_parsed") or job.get("date")),
        }
        jobs.append(parsed_job)
    
    # --- OFFRES TANITJOBS (MongoDB) ---
    for job in db_tanit.find().limit(100):
        parsed_job = {
            "id": str(job.get("_id")),
            "source": "TanitJobs.com",
            "title": job.get("title") or "Titre non disponible",
            "company": job.get("company") or "Entreprise",
            "location": job.get("location") or "Tunisie",
            "description": job.get("description") or "",
            "url_final": job.get("url") or job.get("url_final") or "#",
            "logo": None,
            "contract_type": job.get("contract_type"),
            "salary": None,
            "industry": None,
            "parsed_date": parse_date(job.get("date") or str(job.get("scraped_at"))),
            "is_internal": False,
            "is_new": is_new_job(job.get("date")),
        }
        jobs.append(parsed_job)
    
    # --- OFFRES INTERNES (votre plateforme) ---
     # --- OFFRES INTERNES (votre plateforme) ---
    internal_jobs = JobDocument.objects.filter(status='PUBLISHED')
    
    for job in internal_jobs:
        # Calculer le score de matching si candidat connecté
        match_score = None
        if request.user.is_authenticated and request.user.role == 'candidate':
            try:
                candidate = CandidateDocument.objects.get(id=request.user.mongo_id)
                match_score = calculate_match_score(candidate, job)
            except CandidateDocument.DoesNotExist:
                pass
        
        parsed_job = {
            "id": str(job.id),
            "source": "Plateforme RH",  # Pour distinguer
            "title": job.title,
            "company": job.company_name,
            "location": job.location,
            "description": job.description,
            "url_final": f"/jobs/{job.id}/",  # URL interne (à créer plus tard)
            "logo": None,  # À améliorer avec le logo de l'entreprise
            "contract_type": dict(job._fields['contract_type'].choices).get(job.contract_type),
            "salary": job.get_salary_range() if job.salary_min else None,
            "industry": job.industry,
            "parsed_date": job.published_at,
            "is_internal": True,
            "is_new": job.is_new(),
            "match_score": match_score,
            "applicants_count": job.applications_count,
        }
        jobs.append(parsed_job)
    # Tri par date décroissante
    jobs = sorted(jobs, key=lambda x: x["parsed_date"], reverse=True)
    
    # Filtres depuis la requête GET
    location_filter = request.GET.get('location', '').lower()
    contract_filter = request.GET.get('contract', '').lower()
    source_filter = request.GET.get('source', '').lower()
    search_query = request.GET.get('q', '').lower()
    
    # Appliquer les filtres
    if location_filter:
        jobs = [j for j in jobs if location_filter in j['location'].lower()]
    
    if contract_filter:
        jobs = [j for j in jobs if j['contract_type'] and contract_filter in j['contract_type'].lower()]
    
    if source_filter:
        if source_filter == 'platform':
            jobs = [j for j in jobs if j['is_internal']]
        else:
            jobs = [j for j in jobs if source_filter in j['source'].lower()]
    
    if search_query:
        jobs = [j for j in jobs if (
            search_query in j['title'].lower() or
            search_query in j['company'].lower() or
            search_query in j['description'].lower()
        )]
    
    context = {
        "jobs": jobs,
        "total_count": len(jobs),
    }
    
    return render(request, "jobs/all_jobs.html", context)


# ==================== VUES POUR CANDIDATS ====================

@login_required
def job_detail(request, job_id):
    """
    Vue détaillée d'une offre interne
    """
    try:
        job = JobDocument.objects.get(id=job_id, status='PUBLISHED')
    except JobDocument.DoesNotExist:
        messages.error(request, "Cette offre n'existe pas ou n'est plus disponible.")
        return redirect('all_jobs')
    
    # Incrémenter le compteur de vues
    job.increment_views()
    
    # Calculer le score de matching si candidat
    match_score = None
    has_applied = False
    
    if request.user.is_authenticated and request.user.role == 'candidate':
        try:
            candidate = CandidateDocument.objects.get(id=request.user.mongo_id)
            match_score = calculate_match_score(candidate, job)
            
            # Vérifier si déjà candidaté
            from .models import ApplicationDocument
            has_applied = ApplicationDocument.objects.filter(
                job_id=job.id,
                candidate_id=candidate.id
            ).count() > 0
            
        except CandidateDocument.DoesNotExist:
            pass
    
    context = {
        'job': job,
        'match_score': match_score,
        'has_applied': has_applied,
    }
    
    return render(request, 'jobs/job_detail.html', context)
@login_required
def apply_to_job(request, job_id):
    """
    Postuler à une offre interne
    """
    from .forms import ApplicationForm
    
    # Vérifier que l'utilisateur est un candidat
    if request.user.role != 'candidate':
        messages.error(request, "Seuls les candidats peuvent postuler.")
        return redirect('all_jobs')
    
    # Récupérer l'offre
    try:
        job = JobDocument.objects.get(id=job_id, status='PUBLISHED')
    except JobDocument.DoesNotExist:
        messages.error(request, "Cette offre n'existe pas ou n'est plus disponible.")
        return redirect('all_jobs')
    
    # Récupérer le candidat
    try:
        candidate = CandidateDocument.objects.get(id=request.user.mongo_id)
    except CandidateDocument.DoesNotExist:
        messages.error(request, "Profil candidat invalide.")
        return redirect('all_jobs')
    
    # Vérifier si déjà candidaté
    existing_application = ApplicationDocument.objects.filter(
        job_id=job.id,
        candidate_id=candidate.id
    ).first()
    
    if existing_application:
        messages.warning(request, "Vous avez déjà postulé à cette offre.")
        return redirect('job_detail', job_id=job_id)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)  # ✅ RETIRER request.FILES
        
        if form.is_valid():
            # Calculer le score de matching
            match_score = calculate_match_score(candidate, job)
            
            # Analyse IA de la candidature
            ai_analysis = analyze_application_with_ai(candidate, job)
            
            # Créer la candidature
            application = ApplicationDocument(
                job_id=job.id,
                job_title=job.title,
                company_name=job.company_name,
                candidate_id=candidate.id,
                candidate_name=f"{candidate.first_name} {candidate.last_name}",
                candidate_email=candidate.email,
                cover_letter=form.cleaned_data.get('cover_letter', ''),
                cv_url=candidate.cv_url,  # ✅ Utilise le CV du profil
                ai_match_score=match_score,
                ai_analysis=ai_analysis,
                status='SUBMITTED',
                applied_at=datetime.now(),
                updated_at=datetime.now()
            )
            application.save()
            
            # Incrémenter le compteur de candidatures
            job.increment_applications()
            
            messages.success(
                request, 
                f"🎉 Candidature envoyée avec succès ! Score de matching : {match_score}%"
            )
            return redirect('candidate_dashboard')
    else:
        form = ApplicationForm()
    
    # Calculer le score de matching pour affichage
    match_score = calculate_match_score(candidate, job)
    
    context = {
        'form': form,
        'job': job,
        'candidate': candidate,
        'match_score': match_score,
    }
    
    return render(request, 'jobs/apply.html', context)

@login_required
def save_job(request, job_id):
    """
    Sauvegarder une offre dans les favoris (AJAX)
    """
    if request.method == 'POST' and request.user.role == 'candidate':
        # Décommentez si vous avez un model SavedJob
        """
        job = get_object_or_404(InternalJob, id=job_id)
        candidate = request.user.candidate
        
        saved_job, created = SavedJob.objects.get_or_create(
            candidate=candidate,
            job=job
        )
        
        if not created:
            # Si déjà sauvegardé, on le retire
            saved_job.delete()
            return JsonResponse({'saved': False})
        
        return JsonResponse({'saved': True})
        """
        pass
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==================== FONCTIONS UTILITAIRES ====================

def parse_date(value):
    """
    Convertit une date en datetime.
    Si string : tente différents formats.
    Si datetime : renvoie tel quel.
    Sinon renvoie datetime.min
    """
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, str):
        # Liste des formats à tester
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    
    # Si aucun format ne marche, retourner date minimale
    return datetime.min


def is_new_job(date_value):
    """
    Détermine si une offre est "nouvelle" (moins de 3 jours)
    """
    parsed_date = parse_date(date_value)
    
    if parsed_date == datetime.min:
        return False
    
    days_ago = (datetime.now() - parsed_date).days
    return days_ago <= 3


def calculate_match_score(candidate, job):
    """
    Calcule le score de matching entre un candidat et une offre (0-100)
    Utilise l'IA pour comparer les compétences
    
    TODO: Implémenter avec OpenAI ou un modèle ML
    """
    # Version simple basée sur les compétences
    candidate_skills = set([s.lower() for s in candidate.skills])
    job_skills = set([s.lower() for s in job.required_skills])
    
    if not job_skills:
        return 50  # Score par défaut si pas de compétences définies
    
    # Intersection des compétences
    matching_skills = candidate_skills.intersection(job_skills)
    
    # Calcul du score
    score = int((len(matching_skills) / len(job_skills)) * 100)
    
    # Bonus pour l'expérience
    if candidate.experience_years >= job.experience_min:
        score = min(100, score + 10)
    
    # Bonus pour la localisation
    if candidate.location.lower() in job.location.lower():
        score = min(100, score + 5)
    
    return score


def analyze_application_with_ai(candidate, job):
    """
    Analyse une candidature avec l'IA et retourne des insights
    
    TODO: Implémenter avec OpenAI GPT
    """
    analysis = {
        'strengths': [],
        'weaknesses': [],
        'recommendations': ''
    }
    
    # Exemple simple - À remplacer par un vrai appel API
    candidate_skills = set([s.lower() for s in candidate.skills])
    job_skills = set([s.lower() for s in job.required_skills])
    
    matching_skills = candidate_skills.intersection(job_skills)
    missing_skills = job_skills - candidate_skills
    
    analysis['strengths'] = [
        f"Maîtrise de {skill}" for skill in list(matching_skills)[:3]
    ]
    
    analysis['weaknesses'] = [
        f"Compétence manquante: {skill}" for skill in list(missing_skills)[:3]
    ]
    
    if missing_skills:
        analysis['recommendations'] = f"Nous recommandons de suivre une formation en {', '.join(list(missing_skills)[:2])}"
    else:
        analysis['recommendations'] = "Profil excellent pour ce poste !"
    
    return analysis


def get_similar_jobs(job, limit=5):
    """
    Trouve des offres similaires basées sur les compétences et le secteur
    
    TODO: Améliorer avec un algorithme de recommandation plus sophistiqué
    """
    # Décommentez si vous avez le model
    """
    similar = InternalJob.objects.filter(
        status='published',
        industry=job.industry
    ).exclude(id=job.id)[:limit]
    
    return similar
    """
    return []


# ==================== VUES POUR RECRUTEURS ====================

@login_required
def create_job(request):
    """Publier une nouvelle offre (recruteurs uniquement)"""
    
    # Vérifier que l'utilisateur est un recruteur
    if request.user.role != 'recruiter':
        messages.error(request, "Seuls les recruteurs peuvent publier des offres.")
        return redirect('all_jobs')
    
    # Récupérer le document recruteur
    try:
        recruiter = RecruiterDocument.objects.get(id=request.user.mongo_id)
        company = CompanyDocument.objects.get(id=recruiter.company_id)
    except (RecruiterDocument.DoesNotExist, CompanyDocument.DoesNotExist):
        messages.error(request, "Profil recruteur invalide.")
        return redirect('recruiter_dashboard')
    
    if request.method == 'POST':
        form = JobCreationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Calculer la date d'expiration
            expires_at = None
            if data.get('expires_in_days'):
                expires_at = datetime.now() + timedelta(days=data['expires_in_days'])
            
            # Créer l'offre
            job = JobDocument(
                company_id=company.id,
                company_name=company.name,
                recruiter_id=recruiter.id,
                title=data['title'],
                description=data['description'],
                location=data['location'],
                contract_type=data['contract_type'],
                work_mode=data['work_mode'],
                salary_min=data.get('salary_min'),
                salary_max=data.get('salary_max'),
                salary_period=data['salary_period'],
                required_skills=data.get('required_skills', []),
                experience_min=data['experience_min'],
                experience_max=data.get('experience_max'),
                education_level=data.get('education_level'),
                industry=data.get('industry'),
                status='PUBLISHED',
                published_at=datetime.now(),
                expires_at=expires_at,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            job.save()
            
            messages.success(request, f"✅ Offre '{job.title}' publiée avec succès !")
            return redirect('recruiter_dashboard')
    else:
        form = JobCreationForm()
    
    context = {
        'form': form,
        'recruiter': recruiter,
        'company': company
    }
    
    return render(request, 'jobs/create_job.html', context)

@login_required
def manage_applications(request, job_id):
    """
    Gérer les candidatures pour une offre (recruteurs uniquement)
    """
    if request.user.role != 'recruiter':
        messages.error(request, "Accès refusé.")
        return redirect('all_jobs')
    
    # TODO: Implémenter la gestion des candidatures
    """
    job = get_object_or_404(InternalJob, id=job_id, company=request.user.recruiter.company)
    applications = Application.objects.filter(job=job).select_related('candidate').order_by('-ai_match_score')
    
    context = {
        'job': job,
        'applications': applications,
    }
    
    return render(request, 'jobs/manage_applications.html', context)
    """
    pass