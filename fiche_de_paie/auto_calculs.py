from decimal import Decimal, ROUND_HALF_UP
from .auto_config import REGLES_AUTOMATIQUES, SEUILS_AUTOMATIQUES

# === Taux cotisations salarié ===
TAUX_ASSURANCES = Decimal('0.05')       # Assurances sociales
TAUX_SUPP = Decimal('0.0143')           # Cotisation supplémentaire assurance maladie
TAUX_PENSIONS = Decimal('0.0275')       # Régime de pensions
TAUX_CHOMAGE = Decimal('0.005')         # Assurance chômage

# === Taux cotisations employeur ===
TAUX_ASSURANCES_EMPLOYEUR = Decimal('0.13')
TAUX_SUPP_EMPLOYEUR = Decimal('0.0057')
TAUX_PENSIONS_EMPLOYEUR = Decimal('0.025')
TAUX_CHOMAGE_EMPLOYEUR = Decimal('0.005')
TAUX_MAJORATION_EMPLOYEUR = Decimal('0.005')

# === Barème IRPP 2025 ===
BARÈME_IRPP = [
    (0, 5000, 0),           # 0-5000 TND : 0%
    (5000.001, 10000, 0.15), # 5001-10000 TND : 15%
    (10000.001, 20000, 0.25), # 10001-20000 TND : 25%
    (20000.001, 30000, 0.30), # 20001-30000 TND : 30%
    (30000.001, 40000, 0.33), # 30001-40000 TND : 33%
    (40000.001, 50000, 0.36), # 40001-50000 TND : 36%
    (50000.001, 70000, 0.38), # 50001-70000 TND : 38%
    (70000.001, float('inf'), 0.40), # +70000 TND : 40%
]

CSS_TAUX = Decimal('0.005')  # Contribution sociale de solidarité 0,5%

# === Calcul cotisations CNSS ===
def calcul_cotisations(total_brut):
    total_brut = Decimal(total_brut)

    # Cotisations salariales
    cot_salarie = {
        'assurances': (total_brut * TAUX_ASSURANCES).quantize(Decimal('0.01')),
        'supp': (total_brut * TAUX_SUPP).quantize(Decimal('0.01')),
        'pensions': (total_brut * TAUX_PENSIONS).quantize(Decimal('0.01')),
        'chomage': (total_brut * TAUX_CHOMAGE).quantize(Decimal('0.01')),
    }
    total_salarie = sum(cot_salarie.values())

    # Cotisations employeur
    cot_employeur = {
        'assurances': (total_brut * TAUX_ASSURANCES_EMPLOYEUR).quantize(Decimal('0.01')),
        'supp': (total_brut * TAUX_SUPP_EMPLOYEUR).quantize(Decimal('0.01')),
        'pensions': (total_brut * TAUX_PENSIONS_EMPLOYEUR).quantize(Decimal('0.01')),
        'chomage': (total_brut * TAUX_CHOMAGE_EMPLOYEUR).quantize(Decimal('0.01')),
        'majoration_loi_74_101': (total_brut * TAUX_MAJORATION_EMPLOYEUR).quantize(Decimal('0.01')),
    }
    total_employeur = sum(cot_employeur.values())

    return {
        'salarie': cot_salarie,
        'retenue_cnss': total_salarie,  # nombre Decimal
        'employeur': cot_employeur,
        'total_cotisations_patronales': total_employeur
    }

# === Calcul IRPP 2025 ===
def calcul_irpp(salaire_mensuel_net_imposable):
    """Calcule l'IRPP sur base ANNUELLE"""
    salaire_mensuel = Decimal(salaire_mensuel_net_imposable)
    
    # Conversion en base annuelle
    base_imposable_annuelle = salaire_mensuel * 12
    
    irpp_annuel = Decimal('0')
    
    # Application du barème sur base ANNUELLE
    for min_val, max_val, taux in BARÈME_IRPP:
        if base_imposable_annuelle > Decimal(str(min_val)):
            tranche = min(base_imposable_annuelle, Decimal(str(max_val))) - Decimal(str(min_val))
            irpp_annuel += (tranche * Decimal(str(taux))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Conversion en mensuel
    irpp_mensuel = (irpp_annuel / 12).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return irpp_mensuel

# === Calcul CSS 0,5% si revenu annuel net imposable > 5000 TND ===
def calcul_css(salaire_brut):
    salaire_annuel = Decimal(salaire_brut) * 12
    if salaire_annuel > 5000:
        return (Decimal(salaire_brut) * CSS_TAUX).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return Decimal('0.00')

# === Classe principale de calcul automatique ===
class CalculateurPaieAuto:
    def __init__(self, salaire_base, annees_anciennete=0):
        self.salaire_base = Decimal(str(salaire_base))
        self.annees_anciennete = annees_anciennete
        self.resultats = {}

    # --- Prime ancienneté ---
    def calculer_prime_anciennete(self):
        regle = REGLES_AUTOMATIQUES['prime_anciennete']
        taux = Decimal('0')
        for seuil, taux_seuil in reversed(regle['echelons']):
            if self.annees_anciennete >= seuil:
                taux = taux_seuil
                break
        montant = (self.salaire_base * taux).quantize(Decimal('0.01'))
        return {'montant': montant, 'libelle': regle['libelle']} if montant > 0 else None

    # --- Tous les gains (primes) ---
    def calculer_tous_les_gains(self):
        gains = {}
        total_brut = self.salaire_base

        # Liste des primes à calculer
        primes = ['prime_presence', 'indemn_transport', 'prime_panier', 'prime_rendement']
        for prime in primes:
            regle = REGLES_AUTOMATIQUES[prime]
            montant = (self.salaire_base * regle['valeur']).quantize(Decimal('0.01'))
            # Vérification des seuils pour certaines primes
            if prime in ['prime_presence', 'prime_rendement']:
                seuil = SEUILS_AUTOMATIQUES[f'{prime}_seuil']
                if self.salaire_base < seuil:
                    continue
            gains[prime] = {'montant': montant, 'libelle': regle['libelle']}
            total_brut += montant

        # Prime ancienneté
        prime_anciennete = self.calculer_prime_anciennete()
        if prime_anciennete:
            gains['prime_anciennete'] = prime_anciennete
            total_brut += prime_anciennete['montant']

        self.resultats['total_brut'] = total_brut
        self.resultats['gains'] = gains
        return self.resultats

    # --- Calcul salaire net ---
    def calculer_salaire_net(self):
        total_brut = self.resultats.get('total_brut', self.salaire_base)
        cotisations = calcul_cotisations(total_brut)
        irpp = calcul_irpp(total_brut)
        css = calcul_css(total_brut)
        salaire_net = total_brut - cotisations['retenue_cnss'] - irpp - css  # tous Decimal

        self.resultats.update({
            'cotisations': cotisations,
            'irpp': irpp,
            'css': css,
            'salaire_net': salaire_net
        })
        return self.resultats
