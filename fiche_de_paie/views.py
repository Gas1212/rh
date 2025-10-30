from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from fpdf import FPDF   
from .forms import BulletinPaieForm
from .auto_calculs import CalculateurPaieAuto, calcul_cotisations, calcul_irpp, calcul_css

# --- Fonction de calcul complète CORRIGÉE ---
def calcul_auto(data):
    """Calcul automatique complet du bulletin de paie"""
    # Extraction des données
    s_base = Decimal(str(data.get('salaire_base', 0)))
    chef_famille = data.get('chef_famille', False)
    enfants = int(data.get('enfants', 0))
    annees_anciennete = int(data.get('annees_anciennete', 0))
    
    # Initialisation du calculateur
    calculateur = CalculateurPaieAuto(s_base, annees_anciennete)
    calculateur.calculer_tous_les_gains()
    resultats = calculateur.calculer_salaire_net()

    total_brut = resultats['total_brut']
    cotisations = resultats['cotisations']
    gains = resultats['gains']
    
    # Calcul brut imposable MENSUEL
    brut_imposable_mensuel = total_brut - cotisations['retenue_cnss']
    
    # Calcul déductions fiscales MENSUELLES
    ded_situation_mensuel = Decimal('0')
    if chef_famille:
        ded_situation_mensuel += Decimal('25')  # 300/12 = 25 TND par mois
    ded_situation_mensuel += Decimal('8.33') * enfants  # 100/12 ≈ 8.33 TND par enfant/mois
    
    frais_prof_mensuel = (brut_imposable_mensuel * Decimal('0.10')).quantize(Decimal('0.001'))
    autres_deductions = Decimal(str(data.get('autres_deductions', 0)))
    avance = Decimal(str(data.get('avance', 0)))
    
    # Base imposable nette MENSUELLE
    base_imposable_nette_mensuel = max(
        brut_imposable_mensuel - ded_situation_mensuel - frais_prof_mensuel,
        Decimal('0')
    )
    
    # ✅ CORRECTION : Calcul IRPP sur base MENSUELLE (la fonction gère la conversion annuelle)
    irpp = calcul_irpp(base_imposable_nette_mensuel)
    
    # ✅ CORRECTION : Calcul CSS sur base MENSUELLE
    css = calcul_css(brut_imposable_mensuel)
    
    # Total impôts
    total_impots = irpp + css
    
    # Calcul cohérent du net à payer
    net_a_payer = total_brut - cotisations['retenue_cnss'] - total_impots - avance - autres_deductions

    # Mise à jour du dictionnaire data
    data.update({
        'salaire_base': float(s_base),
        'total_brut': float(total_brut),
        'brut_imposable': float(brut_imposable_mensuel),
        'retenue_cnss': float(cotisations['retenue_cnss']),
        'total_cotisations_patronales': float(cotisations['total_cotisations_patronales']),
        'irpp': float(irpp),
        'css': float(css),
        'total_impots': float(total_impots),
        'salaire_net': float(total_brut - cotisations['retenue_cnss'] - total_impots),
        'net_a_payer': float(net_a_payer),
        'ded_situation': float(ded_situation_mensuel),
        'frais_prof': float(frais_prof_mensuel),
        'base_imposable_nette': float(base_imposable_nette_mensuel),
        'date_generation': datetime.now().strftime('%d/%m/%Y'),
    })

    # Ajouter cotisations salariales individuellement
    for k, v in cotisations['salarie'].items():
        data[f'cotisation_{k}'] = float(v)
    
    # Ajouter cotisations patronales individuellement
    for k, v in cotisations['employeur'].items():
        data[f'patronale_{k}'] = float(v)

    # Ajouter primes individuelles
    for k, v in gains.items():
        data[k] = float(v['montant'])

    return data
  
# --- Génération PDF améliorée avec FPDF ---
def generate_pdf_fpdf(data):
    """Génère un PDF professionnel avec FPDF"""
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Couleurs personnalisées
    color_header = (52, 73, 94)      # Bleu foncé
    color_section = (236, 240, 241)  # Gris clair
    color_red = (231, 76, 60)        # Rouge
    color_green = (39, 174, 96)      # Vert
    
    # --- En-tête ---
    pdf.set_fill_color(*color_header)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, data.get('societe', 'SOCIETE DIAMOND'), ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, f"Bulletin de Paie - {data.get('mois', '-')} {data.get('annee', '-')}", ln=True, align='C')
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"CNSS : {data.get('cnss', '-')}", ln=True, align='C')
    pdf.ln(5)
    
    # --- Informations employé ---
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "INFORMATIONS EMPLOYE", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    
    # Tableau informations
    info_data = [
        ["Nom & Prenom:", str(data.get('nom_prenom', '-')), "Matricule:", str(data.get('matricule', '-'))],
        ["Emploi:", str(data.get('emploi', '-')), "CIN:", str(data.get('cin', '-'))],
    ]
    
    for row in info_data:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(45, 6, row[0], border=1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(50, 6, row[1], border=1)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 6, row[2], border=1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, row[3], border=1, ln=True)
    
    # Statut familial
    statut = "Chef de famille" if data.get('chef_famille') else "Celibataire"
    enfants = f" - {data.get('enfants', 0)} enfant(s)" if data.get('enfants', 0) > 0 else ""
    pdf.set_font("Arial", "B", 10)
    pdf.cell(45, 6, "Statut familial:", border=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"{statut}{enfants}", border=1, ln=True)
    pdf.ln(5)
    
    # --- Gains et Primes ---
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "GAINS ET PRIMES", ln=True, fill=True)
    
    # En-tête tableau
    pdf.set_fill_color(*color_header)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(130, 7, "Designation", border=1, fill=True)
    pdf.cell(0, 7, "Montant (TND)", border=1, align='R', fill=True, ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 10)
    
    # Lignes gains
    primes = [
        ("Salaire de base", data.get('salaire_base', 0)),
        ("Prime de presence", data.get('prime_presence', 0)),
        ("Indemnite de transport", data.get('indemn_transport', 0)),
        ("Prime panier", data.get('prime_panier', 0)),
        ("Prime de rendement", data.get('prime_rendement', 0)),
        ("Prime d'anciennete", data.get('prime_anciennete', 0)),
        ("Heures supplementaires", data.get('heures_supp', 0)),
    ]
    
    for libelle, montant in primes:
        if montant and montant > 0:
            pdf.cell(130, 6, libelle, border=1)
            pdf.cell(0, 6, f"{montant:.3f}", border=1, align='R', ln=True)
    
    # Total brut
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(130, 7, "TOTAL BRUT", border=1, fill=True)
    pdf.cell(0, 7, f"{data.get('total_brut', 0):.3f}", border=1, align='R', fill=True, ln=True)
    pdf.ln(5)
    
    # --- Cotisations Sociales ---
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "COTISATIONS SOCIALES", ln=True, fill=True)
    
    # En-tête tableau
    pdf.set_fill_color(*color_header)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(90, 7, "Designation", border=1, fill=True)
    pdf.cell(50, 7, "Part Salariale", border=1, align='R', fill=True)
    pdf.cell(0, 7, "Part Patronale", border=1, align='R', fill=True, ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    
    cotisations = [
        ("Assurances sociales (5%)", data.get('cotisation_assurances', 0), data.get('patronale_assurances', 0)),
        ("Cotisation supp. maladie (1.43%)", data.get('cotisation_supp', 0), data.get('patronale_supp', 0)),
        ("Regime de pensions (2.75%)", data.get('cotisation_pensions', 0), data.get('patronale_pensions', 0)),
        ("Assurance chomage (0.5%)", data.get('cotisation_chomage', 0), data.get('patronale_chomage', 0)),
        ("Majoration loi 74-101 (0.5%)", 0, data.get('patronale_majoration_loi_74_101', 0)),
    ]
    
    for libelle, part_s, part_p in cotisations:
        pdf.cell(90, 6, libelle, border=1)
        pdf.cell(50, 6, f"{part_s:.3f}" if part_s > 0 else "-", border=1, align='R')
        pdf.cell(0, 6, f"{part_p:.3f}", border=1, align='R', ln=True)
    
    # Total cotisations
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(90, 7, "TOTAL COTISATIONS", border=1, fill=True)
    pdf.cell(50, 7, f"{data.get('retenue_cnss', 0):.3f}", border=1, align='R', fill=True)
    pdf.cell(0, 7, f"{data.get('total_cotisations_patronales', 0):.3f}", border=1, align='R', fill=True, ln=True)
    pdf.ln(5)
    
    # --- Impôts et Contributions ---
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "IMPOTS ET CONTRIBUTIONS", ln=True, fill=True)
    
    # En-tête tableau
    pdf.set_fill_color(*color_header)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(130, 7, "Designation", border=1, fill=True)
    pdf.cell(0, 7, "Montant (TND)", border=1, align='R', fill=True, ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 10)
    
    # Calcul imposable
    pdf.cell(130, 6, "Salaire brut imposable", border=1)
    pdf.cell(0, 6, f"{data.get('brut_imposable', 0):.3f}", border=1, align='R', ln=True)
    
    if data.get('ded_situation', 0) > 0:
        pdf.cell(130, 6, "Deduction situation familiale", border=1)
        pdf.set_text_color(*color_red)
        pdf.cell(0, 6, f"-{data.get('ded_situation', 0):.3f}", border=1, align='R', ln=True)
        pdf.set_text_color(0, 0, 0)
    
    if data.get('frais_prof', 0) > 0:
        pdf.cell(130, 6, "Frais professionnels (10%)", border=1)
        pdf.set_text_color(*color_red)
        pdf.cell(0, 6, f"-{data.get('frais_prof', 0):.3f}", border=1, align='R', ln=True)
        pdf.set_text_color(0, 0, 0)
    
    # Base imposable nette
    pdf.set_fill_color(248, 249, 250)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(130, 6, "Base imposable nette", border=1, fill=True)
    pdf.cell(0, 6, f"{data.get('base_imposable_nette', 0):.3f}", border=1, align='R', fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    
    # IRPP et CSS
    pdf.cell(130, 6, "IRPP (Impot sur le revenu)", border=1)
    pdf.set_text_color(*color_red)
    pdf.cell(0, 6, f"{data.get('irpp', 0):.3f}", border=1, align='R', ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.cell(130, 6, "CSS (Contribution solidarite - 0.5%)", border=1)
    pdf.set_text_color(*color_red)
    pdf.cell(0, 6, f"{data.get('css', 0):.3f}", border=1, align='R', ln=True)
    
    # Total impôts
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(130, 7, "TOTAL IMPOTS", border=1, fill=True)
    pdf.set_text_color(*color_red)
    pdf.cell(0, 7, f"{data.get('total_impots', 0):.3f}", border=1, align='R', fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # --- Récapitulatif Final ---
    pdf.set_fill_color(*color_section)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "RECAPITULATIF", ln=True, fill=True)
    
    pdf.set_font("Arial", "", 10)
    recap_data = [
        ("Salaire brut total", data.get('total_brut', 0), False),
        ("Cotisations sociales salariales", data.get('retenue_cnss', 0), True),
        ("IRPP", data.get('irpp', 0), True),
        ("CSS", data.get('css', 0), True),
    ]
    
    if data.get('avance', 0) > 0:
        recap_data.append(("Avances et acomptes", data.get('avance', 0), True))
    
    if data.get('autres_deductions', 0) > 0:
        recap_data.append(("Autres deductions", data.get('autres_deductions', 0), True))
    
    for libelle, montant, is_negative in recap_data:
        pdf.cell(130, 6, libelle, border=1)
        if is_negative:
            pdf.set_text_color(*color_red)
            pdf.cell(0, 6, f"-{montant:.3f}", border=1, align='R', ln=True)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(0, 6, f"{montant:.3f}", border=1, align='R', ln=True)
    
    # NET À PAYER
    pdf.set_fill_color(39, 174, 96)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(130, 10, "NET A PAYER", border=1, fill=True)
    pdf.cell(0, 10, f"{data.get('net_a_payer', 0):.3f} TND", border=1, align='R', fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # --- Signatures ---
    y_position = pdf.get_y()
    
    # Signature responsable
    pdf.set_xy(20, y_position)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 6, "Le responsable", align='C', ln=True)
    pdf.set_x(20)
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 6, "Signature et cachet", align='C')
    
    # Signature employé
    pdf.set_xy(110, y_position)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 6, "L'employe", align='C', ln=True)
    pdf.set_xy(110, y_position + 6)
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 6, "Signature", align='C')
    
    pdf.ln(15)
    
    # --- Pied de page ---
    pdf.set_y(-20)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 5, f"Bulletin etabli le {data.get('date_generation', '-')} - Conforme a la legislation tunisienne 2025", align='C')
    
    return pdf.output(dest='S').encode('latin1')


# --- Vue principale de génération ---
@csrf_exempt
def generate_paie(request):
    """Vue pour générer un bulletin de paie PDF"""
    if request.method == 'POST':
        form = BulletinPaieForm(request.POST)
        
        if not form.is_valid():
            return render(request, 'fiche_de_paie/formulaire_auto.html', {
                'form': form,
                'errors': form.errors
            })
        
        # Calcul automatique
        data = calcul_auto(form.cleaned_data)
        
        try:
            # Génération du PDF
            pdf_bytes = generate_pdf_fpdf(data)
            
            # Réponse HTTP avec le PDF
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            nom_fichier = f"bulletin_paie_{data.get('nom_prenom', 'employe').replace(' ', '_')}_{data.get('mois', '')}_{data.get('annee', '')}.pdf"
            response['Content-Disposition'] = f'inline; filename="{nom_fichier}"'
            
            return response
            
        except Exception as e:
            return HttpResponse(f"Erreur lors de la generation du PDF : {e}", status=500)
    
    # GET : affichage du formulaire
    return render(request, 'fiche_de_paie/formulaire_auto.html', {
        'form': BulletinPaieForm()
    })


# --- Vue de prévisualisation HTML ---
def preview_bulletin(request):
    """Prévisualisation HTML du bulletin avant génération PDF"""
    if request.method == 'POST':
        form = BulletinPaieForm(request.POST)
        
        if form.is_valid():
            data = calcul_auto(form.cleaned_data)
            return render(request, 'fiche_de_paie/bulletin.html', {'data': data})
        else:
            return render(request, 'fiche_de_paie/formulaire_auto.html', {
                'form': form,
                'errors': form.errors
            })
    
    return render(request, 'fiche_de_paie/formulaire_auto.html', {
        'form': BulletinPaieForm()
    })


# --- API AJAX pour calcul automatique ---
@csrf_exempt
def calcul_auto_ajax(request):
    """API AJAX pour calculer automatiquement les montants"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Methode non autorisee'}, status=405)
    
    try:
        # Récupération des données POST
        post_data = request.POST.dict()
        
        # Calcul automatique
        data = calcul_auto(post_data)
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# --- Simulateur simplifié ---
# --- Simulateur simplifié ALTERNATIF ---
def simulateur_paie(request):
    """Simulateur simple de salaire net - Version simplifiée mais cohérente"""
    if request.method == 'POST':
        try:
            salaire_base = Decimal(request.POST.get('salaire_brut', 0))
            chef_famille = request.POST.get('chef_famille', 'non') == 'oui'
            enfants = int(request.POST.get('enfants', 0))
            
            # ✅ CALCULS SIMILAIRES À calcul_auto mais simplifiés
            # 1. Cotisations sociales (identique)
            cotisations = calcul_cotisations(salaire_base)
            
            # 2. Brut imposable (identique)
            brut_imposable = salaire_base - cotisations['retenue_cnss']
            
            # 3. Déductions familiales (identique mais mensuelles)
            ded_situation_mensuel = Decimal('0')
            if chef_famille:
                ded_situation_mensuel += Decimal('25')  # 300/12
            ded_situation_mensuel += Decimal('8.33') * enfants  # 100/12
            
            # 4. Frais professionnels (identique)
            frais_prof_mensuel = (brut_imposable * Decimal('0.10')).quantize(Decimal('0.001'))
            
            # 5. Base imposable nette (identique)
            base_imposable_nette_mensuel = max(
                brut_imposable - ded_situation_mensuel - frais_prof_mensuel,
                Decimal('0')
            )
            
            # 6. IRPP et CSS (IDENTIQUES - utilisent les mêmes fonctions)
            irpp = calcul_irpp(base_imposable_nette_mensuel)
            css = calcul_css(brut_imposable)
            
            # 7. Calculs finaux (identique)
            total_impots = irpp + css
            salaire_net = salaire_base - cotisations['retenue_cnss'] - total_impots
            
            context = {
                'nom': request.POST.get('nom', '-'),
                'prenom': request.POST.get('prenom', '-'),
                'mois': request.POST.get('mois', '-'),
                'chef_famille': chef_famille,
                'enfants': enfants,
                
                # Résultats (cohérents avec la fiche de paie)
                'salaire_brut': float(salaire_base),
                'cotisation_sociale': float(cotisations['retenue_cnss']),
                'salaire_apres_cnss': float(brut_imposable),
                'irpp': float(irpp),
                'css': float(css),
                'retenue_totale': float(total_impots),
                'salaire_net': float(salaire_net),
                'net_a_payer': float(salaire_net),  # Pas d'avance ni autres déductions dans le simulateur simple
                
                # Informations détaillées
                'brut_imposable': float(brut_imposable),
                'base_imposable_nette': float(base_imposable_nette_mensuel),
                'ded_situation': float(ded_situation_mensuel),
                'frais_prof': float(frais_prof_mensuel),
            }
            
            return render(request, 'fiche_de_paie/resultat.html', context)
            
        except Exception as e:
            return render(request, 'fiche_de_paie/formulaire.html', {
                'error': f"Erreur de calcul : {str(e)}"
            })
    
    return render(request, 'fiche_de_paie/formulaire.html')
# --- Vue d'export JSON ---
@csrf_exempt
def export_calculs_json(request):
    """Exporte les calculs de paie en JSON"""
    if request.method == 'POST':
        form = BulletinPaieForm(request.POST)
        
        if form.is_valid():
            data = calcul_auto(form.cleaned_data)
            
            response = JsonResponse(data, json_dumps_params={'indent': 2})
            response['Content-Disposition'] = 'attachment; filename="calculs_paie.json"'
            
            return response
        
        return JsonResponse({'error': 'Donnees invalides', 'errors': form.errors.as_json()}, status=400)
    
    return JsonResponse({'error': 'Methode non autorisee'}, status=405)