# Plan d'implémentation du flux de réservation dans GareCI

## 1. MODÈLE RESERVATION (reservations/models.py)
- [ ] Simplifier les statuts: EN_ATTENTE, CONFIRMEE, ANNULEE
- [ ] Supprimer les statuts: EN_ATTENTE_VALIDATION, VALIDEE, REJETEE, EXPIREE

## 2. RECHERCHE PAR DATE (trips/)
- [ ] trips/views.py - Vérifier le filtrage par date (déjà présent)
- [ ] trips/templates/trips/home.html - Ajouter champ date au formulaire
- [ ] trips/templates/trips/search_results.html - Garder le filtrage par date

## 3. RÉSERVATION (reservations/)
- [ ] reservations/views.py - Modifier reserve() pour rediriger vers paiement
- [ ] reservations/forms.py - Adapter si nécessaire
- [ ] reservations/services.py - Modifier pour créer réservation EN_ATTENTE directement
- [ ] reservations/templates/reservations/reserve.html - Adapter le texte
- [ ] reservations/templates/reservations/paiement.html - Garder (boutons payer/échouer)
- [ ] reservations/templates/reservations/paiement_succes.html - Ajouter download billet
- [ ] reservations/templates/reservations/reservation_list.html - Adapter aux statuts simplifiés
- [ ] reservations/urls.py - Adapter si nécessaire

## 4. BILLET PDF (reservations/ticket.py)
- [ ] Déjà implémenté - vérifier

## 5. DASHBOARD ADMIN (gareci_admin/)
- [ ] gareci_admin/views.py - Modifier reservation_list pour grouper par date
- [ ] gareci_admin/views.py - Ajouter vue admin_voir_billet
- [ ] gareci_admin/templates/dashboard/reservation_list.html - Accordéon par date
- [ ] static/css/gareci_admin/dashboards.css - Styles accordéon
- [ ] gareci_admin/urls.py - Ajouter route admin_voir_billet
