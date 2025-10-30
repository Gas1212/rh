# fiche_de_paie/auto_config.py
from decimal import Decimal

# Configuration des règles automatiques pour les primes et indemnités
REGLES_AUTOMATIQUES = {
    'prime_presence': {
        'type': 'pourcentage',
        'valeur': Decimal('0.05'),  # 5% du salaire de base
        'condition_min': Decimal('1000'),  # Seuil minimum
        'libelle': 'Prime de présence'
    },
    'indemn_transport': {
        'type': 'pourcentage', 
        'valeur': Decimal('0.03'),  # 3% du salaire de base
        'condition_min': Decimal('0'),
        'libelle': 'Indemnité de transport'
    },
    'prime_panier': {
        'type': 'pourcentage',
        'valeur': Decimal('0.02'),  # 2% du salaire de base
        'condition_min': Decimal('0'),
        'libelle': 'Prime panier'
    },
    'prime_rendement': {
        'type': 'pourcentage',
        'valeur': Decimal('0.04'),  # 4% du salaire de base
        'condition_min': Decimal('2000'),  # Seuil pour déclencher
        'libelle': 'Prime de rendement'
    },
    'prime_anciennete': {
        'type': 'echelon',
        'echelons': [
            (Decimal('0'), Decimal('0')),      # 0-2 ans: 0%
            (Decimal('2'), Decimal('0.02')),   # 2-5 ans: 2%
            (Decimal('5'), Decimal('0.05')),   # 5-10 ans: 5%
            (Decimal('10'), Decimal('0.08'))   # 10+ ans: 8%
        ],
        'libelle': 'Prime d\'ancienneté'
    },
    'heures_supp': {
        'type': 'manuel',  # Saisie manuelle
        'libelle': 'Heures supplémentaires'
    }
}

# Seuils pour déclencher certaines primes
SEUILS_AUTOMATIQUES = {
    'prime_rendement_seuil': Decimal('2000'),
    'prime_presence_seuil': Decimal('1000'),
}