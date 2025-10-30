# fiche_de_paie/forms.py
from django import forms

class BulletinPaieForm(forms.Form):
    # Champs de base
    nom_prenom = forms.CharField(max_length=100, required=True, label="Nom et Prénom")
    matricule = forms.CharField(max_length=50, required=False, label="Matricule")
    emploi = forms.CharField(max_length=100, required=False, label="Emploi")
    cin = forms.CharField(max_length=20, required=False, label="CIN")
    cnss = forms.CharField(max_length=50, required=False, label="N° CNSS")
    societe = forms.CharField(max_length=100, required=False, label="Société", initial="SOCIETE DIAMOND")
    annee = forms.IntegerField(required=False, label="Année", initial=2025)
    mois = forms.CharField(max_length=20, required=False, label="Mois")
    
    # Champ principal
    salaire_base = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=True, 
        label="Salaire de base (TND)"
    )
    
    # Ancienneté
    annees_anciennete = forms.IntegerField(
        min_value=0, 
        max_value=50, 
        required=False, 
        initial=0,
        label="Années d'ancienneté"
    )
    
    # Situation familiale
    chef_famille = forms.BooleanField(required=False, label="Chef de famille")
    enfants = forms.IntegerField(min_value=0, required=False, initial=0, label="Nombre d'enfants")
    
    # Primes automatiques
    prime_presence = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=False,
        initial=0,
        label="Prime de présence"
    )
    
    indemn_transport = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=False,
        initial=0,
        label="Indemnité de transport"
    )
    
    prime_panier = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=False,
        initial=0,
        label="Prime panier"
    )
    
    prime_rendement = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=False,
        initial=0,
        label="Prime de rendement"
    )
    
    prime_anciennete = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=False,
        initial=0,
        label="Prime d'ancienneté"
    )
    
    heures_supp = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=False,
        initial=0,
        label="Heures supplémentaires"
    )
    
    # Avances
    avance = forms.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        required=False,
        initial=0,
        label="Avances et acomptes"
    )