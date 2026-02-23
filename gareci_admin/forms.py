from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from reservations.models import ContactMessage
from trips.models import Arret, Depart, EtapeTrajet, Segment, Trip, Ville


class ContactReplyForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["reply"]
        labels = {
            "reply": "Reponse a envoyer au client",
        }
        widgets = {
            "reply": forms.Textarea(attrs={"rows": 5, "placeholder": "Votre reponse..."}),
        }


class TripAdminForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "nom",
            "ville_depart",
            "ville_arrivee",
            "arret_depart",
            "arret_arrivee",
            "price",
            "actif",
        ]

    def save(self, commit=True):
        trip = super().save(commit=False)
        # Keep legacy columns in sync with the modern route fields.
        trip.origin = trip.ville_depart.nom if trip.ville_depart_id else ""
        trip.destination = trip.ville_arrivee.nom if trip.ville_arrivee_id else ""
        if not trip.description:
            trip.description = trip.nom or ""
        if commit:
            trip.save()
        return trip


class BaseEtapeTrajetInlineFormSet(BaseInlineFormSet):
    def _get_active_forms(self):
        active_forms = []
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            segment = form.cleaned_data.get("segment")
            if segment is None:
                continue
            active_forms.append(form)
        return active_forms

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        active_forms = self._get_active_forms()
        active_segments = [form.cleaned_data["segment"] for form in active_forms]

        if not active_segments:
            raise forms.ValidationError("Ajoute au moins une etape de trajet.")

        for idx in range(len(active_segments) - 1):
            current_segment = active_segments[idx]
            next_segment = active_segments[idx + 1]
            if current_segment.arret_arrivee_id != next_segment.arret_depart_id:
                raise forms.ValidationError(
                    "Les segments ne sont pas continus. L'arrivee d'une etape doit etre le depart de la suivante."
                )

        expected_start = getattr(self, "expected_trip_start_id", None)
        expected_end = getattr(self, "expected_trip_end_id", None)

        first_segment = active_segments[0]
        last_segment = active_segments[-1]

        if expected_start and first_segment.arret_depart_id != expected_start:
            raise forms.ValidationError(
                "Le premier segment doit commencer a l'arret de depart du trajet."
            )
        if expected_end and last_segment.arret_arrivee_id != expected_end:
            raise forms.ValidationError(
                "Le dernier segment doit finir a l'arret d'arrivee du trajet."
            )

    def save(self, commit=True):
        instances = super().save(commit=False)

        # Keep formset row order as source of truth for ordre: 1..N
        active_forms = self._get_active_forms()
        ordered_instances = []
        for index, form in enumerate(active_forms, start=1):
            instance = form.instance
            instance.trip = self.instance
            instance.segment = form.cleaned_data["segment"]
            instance.ordre = index
            ordered_instances.append(instance)

        if commit:
            for obj in self.deleted_objects:
                obj.delete()
            for instance in ordered_instances:
                instance.save()
            self.save_m2m()

        return ordered_instances


EtapeTrajetFormSet = inlineformset_factory(
    Trip,
    EtapeTrajet,
    fields=("segment",),
    extra=2,
    can_delete=True,
    formset=BaseEtapeTrajetInlineFormSet,
)


class VilleForm(forms.ModelForm):
    class Meta:
        model = Ville
        fields = ["nom", "code"]


class ArretForm(forms.ModelForm):
    class Meta:
        model = Arret
        fields = ["ville", "nom", "adresse"]


class SegmentForm(forms.ModelForm):
    class Meta:
        model = Segment
        fields = ["arret_depart", "arret_arrivee", "distance_km", "duree_minutes"]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("arret_depart") == cleaned_data.get("arret_arrivee"):
            raise forms.ValidationError("Le depart et l'arrivee d'un segment doivent etre differents.")
        return cleaned_data


class DepartForm(forms.ModelForm):
    class Meta:
        model = Depart
        fields = [
            "trip",
            "bus",
            "heure_depart",
            "heure_arrivee",
            "actif",
        ]
        widgets = {
            "heure_depart": forms.TimeInput(
                attrs={"type": "time"},
                format="%H:%M",
            ),
            "heure_arrivee": forms.TimeInput(
                attrs={"type": "time"},
                format="%H:%M",
            ),
        }

    def clean(self):
        cleaned = super().clean()
        h_depart = cleaned.get("heure_depart")
        h_arrivee = cleaned.get("heure_arrivee")

        if h_depart and h_arrivee and h_arrivee <= h_depart:
            raise forms.ValidationError("L'heure d'arrivee doit etre apres l'heure de depart.")
        return cleaned

    def save(self, commit=True):
        depart = super().save(commit=False)
        if depart.trip_id:
            depart.prix = depart.trip.price
        if commit:
            depart.save()
        return depart
