import django_filters
from ...models import Eleve

class EleveFilter(django_filters.FilterSet):
    class Meta:
        model = Eleve
        fields = ['nom', 'prenom', 'condition_eleve', 'sex']  # Fields to be used for filtering
