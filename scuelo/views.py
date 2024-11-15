# Authentication
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import UpdateView, DeleteView
from django.views.generic import DetailView, ListView, CreateView, TemplateView
from django.db.models import Q, Sum, Prefetch, Count  , F
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseRedirect
from weasyprint import HTML
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum
from datetime import timedelta, datetime
import csv
import io
from django.utils import timezone
import base64
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from django.db import models
from datetime import datetime
from django.db.models import  Case, When, Value
from django.db.models.functions import TruncDay
# Models and Forms
from django.utils.timezone import now
from .forms import (
    PaiementPerStudentForm, EleveUpdateForm, MouvementForm,
    EleveCreateForm, EcoleCreateForm, ClasseCreateForm,
    TarifForm, ClassUpgradeForm, SchoolChangeForm , UniformReservationForm
)
from scuelo.models import (
    Eleve, Classe, Inscription, StudentLog,
    AnneeScolaire, Mouvement, Ecole, Tarif ,UniformReservation
)

# =======================
# 1. Authentication
# =======================
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'scuelo/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



# =======================
# 2. Student Management
# =======================

class SchoolYearManagementView(ListView):
    model = AnneeScolaire
    template_name = 'scuelo/annee_scolaire_manage.html'
    context_object_name = 'school_years'

    # Additional context if needed, e.g., for adding, updating, or deleting years
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You can add extra context if necessary
        return context
    
class AddSchoolYearView(CreateView):
    model = AnneeScolaire
    fields = ['nom', 'nom_bref', 'date_initiale', 'date_finale', 'actuel']
    template_name = 'scuelo/add_school_year.html'
    success_url = reverse_lazy('annee_scolaire_manage')

class EditSchoolYearView(UpdateView):
    model = AnneeScolaire
    fields = ['nom', 'nom_bref', 'date_initiale', 'date_finale', 'actuel']
    template_name = 'scuelo/edit_school_year.html'
    success_url = reverse_lazy('annee_scolaire_manage')


class DeleteSchoolYearView(DeleteView):
    model = AnneeScolaire
    template_name = 'scuelo/delete_school_year.html'
    success_url = reverse_lazy('annee_scolaire_manage')    

@login_required
def select_school_year(request):
    if request.method == 'POST':
        # Get the selected school year from the form
        school_year_id = request.POST.get('school_year')
        if school_year_id:
            # Save the selected school year ID in the session
            request.session['selected_school_year'] = school_year_id
        return redirect('home')  # Redirect to home page after setting the year

    # Fetch all available school years for the dropdown
    all_years = AnneeScolaire.objects.all()
    # Retrieve the currently selected school year from the session if it exists
    current_year_id = request.session.get('selected_school_year')

    return render(request, 'scuelo/select_school_year.html', {
        'all_years': all_years,
        'current_year_id': current_year_id,
    })

@login_required
def home(request):
    # Fetch only internal (non-external) schools
    schools = Ecole.objects.filter(externe=False)
    data = {}

    # Icon mapping for each class category
    icon_mapping = {
        "Maternelle": "child",
        "Primaire": "school",
        "Secondaire": "user-graduate",
        "Lycée": "chalkboard-teacher"
    }
 
    # Get the current school year based on request or use the active year by default
    school_year_id = request.GET.get("school_year")
    if school_year_id:
        current_year = AnneeScolaire.objects.get(id=school_year_id)
    else:
        current_year = AnneeScolaire.objects.filter(actuel=True).first()
    
    all_years = AnneeScolaire.objects.all()

    # Group classes by categories within each school
    for school in schools:
        categories = {
            "Maternelle": [],
            "Primaire": [],
            "Secondaire": [],
            "Lycée": []
        }

        # Filter classes based on the selected school year and categorize
        classes = Classe.objects.filter(ecole=school)
        for classe in classes:
            category_key = None
            if classe.type.type_ecole == 'M':
                category_key = "Maternelle"
            elif classe.type.type_ecole == 'P':
                category_key = "Primaire"
            elif classe.type.type_ecole == 'S':
                category_key = "Secondaire"
            elif classe.type.type_ecole == 'L':
                category_key = "Lycée"
            
            if category_key:
                # Add class along with the corresponding icon
                categories[category_key].append({
                    'classe': classe,
                    'icon': icon_mapping.get(category_key, 'school')
                })

        # Only add school to data if it has classes in at least one category
        if any(categories.values()):
            data[school] = categories

    breadcrumbs = [('/', 'Home')]

    return render(request, 'scuelo/home.html', {
        'data': data,
        'breadcrumbs': breadcrumbs,
        'all_years': all_years,
        'current_year': current_year,
        'page_identifier': 'S01'  # Unique page identifier
    })


@login_required
def class_detail(request, pk):
    # Get the class based on the provided primary key (pk)
    classe = get_object_or_404(Classe, pk=pk)

    # Get all academic years to display in the selection dropdown
    all_annee_scolaires = AnneeScolaire.objects.all()

    # Get the selected academic year, default to the current year if none is selected
    selected_annee_scolaire_id = request.GET.get('annee_scolaire')
    selected_annee_scolaire = get_object_or_404(AnneeScolaire, pk=selected_annee_scolaire_id) if selected_annee_scolaire_id else AnneeScolaire.objects.get(actuel=True)

    # Get students registered in this class during the selected academic year
    inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)
    students = [inscription.eleve for inscription in inscriptions]

    # Calculate total payments for each student and get details of each payment
    for student in students:
        payments = Mouvement.objects.filter(inscription__eleve=student, inscription__classe=classe, inscription__annee_scolaire=selected_annee_scolaire)
        student.total_payment = payments.aggregate(total=Sum('montant'))['total'] or 0
        student.payment_details = payments.values('causal', 'montant', 'date_paye')  # Detailed payment info
        student.tenues = payments.filter(causal='TEN').values('montant')  # Only "tenues" payments
        student.notes = student.note_eleve  # Fetch student's notes if available

    # Calculate the total payment amount for the class in the selected academic year
    total_class_payment = Mouvement.objects.filter(
        inscription__classe=classe,
        inscription__annee_scolaire=selected_annee_scolaire
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Get tarifs related to this class for the selected academic year
    tarifs = Tarif.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)

    # Breadcrumb navigation (for template rendering)
    breadcrumbs = [('/', 'Home'), (reverse('home'), 'Classes'), ('#', classe.nom)]

    return render(request, 'scuelo/students/listperclasse.html', {
        'classe': classe,
        'students': students,  # List of students registered this year
        'tarifs': tarifs,  # Tarifs related to this class for this year
        'breadcrumbs': breadcrumbs,
        'all_annee_scolaires': all_annee_scolaires,  # Pass all academic years for selection
        'selected_annee_scolaire': selected_annee_scolaire,  # Pass the selected academic year
        'total_class_payment': total_class_payment,  # Total amount of payments for the class in the selected year
        'page_identifier': 'S02'  # Unique page identifier
    })

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    inscriptions = Inscription.objects.filter(eleve=student).order_by('date_inscription')
    
    # Filter payments using the correct field relationship
    payments = Mouvement.objects.filter(inscription__eleve=student)
    
    total_payment = payments.aggregate(Sum('montant'))['montant__sum'] or 0
    current_class = student.current_class
    
    # Check if current_class is None
    if current_class:
        breadcrumbs = [
            ('/', 'Home'),
            (reverse('home'), 'Classes'),
            (reverse('class_detail', kwargs={'pk': current_class.pk}), current_class.nom),
            ('#', f"{student.nom} {student.prenom}")
        ]
    else:
        brNeadcrumbs = [
            ('/', 'Home'),
            (reverse('home'), 'Classes'),
            ('#', f"{student.nom} {student.prenom}")
        ]
    
    form = PaiementPerStudentForm()
    logs = StudentLog.objects.filter(student=student).order_by('-timestamp')
    
    # Handle receipt printing
    if request.method == 'POST' and 'print_receipt' in request.POST:
        payment_id = request.POST.get('payment_id')
        payment = get_object_or_404(Mouvement, pk=payment_id)

        # Render receipt template to HTML
        html_string = render_to_string('scuelo/paiements/receipt.html', {'student': student, 'payment': payment})

        # Generate PDF
        html = HTML(string=html_string)
        result = html.write_pdf()

        # Create a HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(result, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=receipt_{student.nom}_{student.prenom}_{payment.id}.pdf'
        
        return response

    return render(request, 'scuelo/students/studentdetail.html', {
        'student': student,
        'inscriptions': inscriptions,
        'payments': payments,
        'total_payment': total_payment,
        'breadcrumbs': breadcrumbs,
        'form': form,
        'logs': logs,
         'page_identifier': 'S03'  # Unique page identifier
    })
 
@login_required
def student_update(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    old_values = student.__dict__.copy()
    if request.method == 'POST':
        form = EleveUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            # Log changes
            new_values = student.__dict__.copy()
            for field, old_value in old_values.items():
                new_value = new_values.get(field)
                if old_value != new_value:
                    StudentLog.objects.create(
                        student=student,
                        user=request.user,
                        action=f"Updated {field}",
                        old_value=str(old_value),
                        new_value=str(new_value)
                    )
            return redirect('student_detail', pk=student.pk)
    else:
        form = EleveUpdateForm(instance=student)
    
    return render(request, 'scuelo/students/studentupdate.html', {'form': form, 'student': student,
                                                                  'page_identifier': 'S13'  })

@method_decorator(login_required, name='dispatch')
class StudentListView(ListView):
    model = Eleve
    template_name = 'scuelo/student_management.html'
    context_object_name = 'students'

    def get_queryset(self):
        return Eleve.objects.all().order_by(
            'inscription__classe__ecole__nom',
            'inscription__classe__nom',
            'nom',
            'prenom'
        ).select_related('inscription__classe__ecole')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schools = Ecole.objects.prefetch_related(
            Prefetch('classe_set', queryset=Classe.objects.prefetch_related(
                Prefetch('inscription_set', queryset=Inscription.objects.select_related('eleve'))
            ))
        ).all()

        for school in schools:
            for classe in school.classe_set.all():
                for inscription in classe.inscription_set.all():
                    eleve = inscription.eleve
                    eleve.total_paiements = Mouvement.objects.filter(inscription=inscription).aggregate(total=Sum('montant'))['total'] or 0

        context['schools'] = schools
         # Add your page identifier here
        context['page_identifier'] = 'S14' 
        return context

@login_required
def class_upgrade(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = ClassUpgradeForm(request.POST)
        if form.is_valid():
            new_class = form.cleaned_data['new_class']
            old_class = student.inscription_set.latest('date_inscription').classe.nom

            # Update the latest inscription to the new class
            latest_inscription = student.inscription_set.latest('date_inscription')
            latest_inscription.classe = new_class
            latest_inscription.save()

            # Log the class upgrade
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Upgraded Class",
                old_value=old_class,
                new_value=new_class.nom
            )
            return redirect('student_detail', pk=student.pk)
    else:
        form = ClassUpgradeForm()

    return render(request, 'scuelo/classe/class_upgrade.html',
                  {'form': form, 'student': student ,  
                    'page_identifier': 'S04' })

@login_required
def change_school(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = SchoolChangeForm(request.POST)
        if form.is_valid():
            old_school = student.inscription_set.latest('date_inscription').classe.ecole.nom
            new_school = form.cleaned_data['new_school']
            # Assuming Inscription model has 'eleve', 'classe', and 'annee_scolaire' fields
            latest_inscription = student.inscription_set.latest('date_inscription')
            latest_inscription.classe.ecole = new_school
            latest_inscription.save()
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Changed School",
                old_value=old_school,
                new_value=new_school.nom
            )
            return redirect('student_detail', pk=student.pk)
    else:
        form = SchoolChangeForm()

    return render(request, 'scuelo/school/change_school.html',
                  {'form': form, 'student': student ,
                    'page_identifier': 'S05' })

@login_required
def offsite_students(request):
    # Fetch inscriptions where the school is not "Bisongo du coeur"
    inscriptions = Inscription.objects.filter(
        ~Q(classe__ecole__nom__iexact="Bisongo du coeur")
    ).select_related('eleve', 'classe__ecole')

    # Compile all students identified as offsite
    offsite_students = []
    for inscription in inscriptions:
        student = inscription.eleve
        student.total_paiements = Mouvement.objects.filter(inscription=inscription).aggregate(total=Sum('montant'))['total'] or 0
        student.school_name = inscription.classe.ecole.nom
        student.condition_eleve = student.get_condition_eleve_display()  # Get condition display name
        offsite_students.append(student)

    # Include students with null `annee_inscr` if their school is offsite
    students_with_null_annee_inscr = Eleve.objects.filter(
        ~Q(inscription__classe__ecole__nom__iexact="Bisongo du coeur"),
        annee_inscr__isnull=True
    )

    # Combine both sets of students into one list
    all_offsite_students = offsite_students 

    context = {
        'all_offsite_students': all_offsite_students,  
        'page_identifier': 'S06' # Combined list of offsite students
    }
    return render(request, 'scuelo/offsite_students.html', context)
@method_decorator(login_required, name='dispatch')
class StudentCreateView(CreateView):
    model = Eleve
    form_class = EleveCreateForm
    template_name = 'scuelo/students/new_student.html'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['breadcrumbs'] = [('/', 'Home'), ('/students/create/', 'Ajouter élève')]
          # Add page identifier
        data['page_identifier'] = 'S15'  # Unique identifier for this page
        
        return data

    def form_valid(self, form):
        eleve = form.save(commit=False)
        eleve.save()
        classe = form.cleaned_data['classe']
        annee_scolaire = form.cleaned_data['annee_scolaire']
        Inscription.objects.create(eleve=eleve, classe=classe, annee_scolaire=annee_scolaire)
        return super().form_valid(form)


# =======================
# 3. Class Management
# =======================
@method_decorator(login_required, name='dispatch')
class ClasseCreateView(CreateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_create.html'

    def form_valid(self, form):
        form.instance.ecole_id = self.kwargs['pk']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('school_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add page identifier for this page
        context['page_identifier'] = 'S16'  # Example page identifier
        return context
    
from django.db.models import Sum

@method_decorator(login_required, name='dispatch')
class ClasseDetailView(DetailView):
    model = Classe
    template_name = 'scuelo/classe/classe_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classe = self.get_object()

        # Get the current academic year
        current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

        # Class Information
        context['classe'] = classe
        context['school_name'] = classe.ecole.nom
        context['teacher'] = None  # Placeholder for when teachers are assigned
        context['notes'] = "Add any specific notes about the class here."  # Placeholder for notes

        # Tariffs for the class and current academic year
        latest_tariffs = Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire).order_by('date_expiration')
        
        # Calculate expected total for each tariff based on PY and CONF students
        py_conf_students_count = Inscription.objects.filter(
            classe=classe,
            annee_scolaire=current_annee_scolaire,
            eleve__cs_py="P",  # Only PY students
            eleve__condition_eleve="CONF"  # Only CONF students
        ).count()

        for tarif in latest_tariffs:
            tarif.expected_total = (tarif.montant * py_conf_students_count) if py_conf_students_count else 0

        context['latest_tariffs'] = latest_tariffs

        # Uniforms (Tenues)
        tenues = Mouvement.objects.filter(inscription__classe=classe, causal='TEN', inscription__annee_scolaire=current_annee_scolaire).aggregate(total=Sum('montant'))['total'] or 0
        context['tenues'] = tenues

        # Total payments for the class
        total_class_payment = Mouvement.objects.filter(inscription__classe=classe, inscription__annee_scolaire=current_annee_scolaire).aggregate(total=Sum('montant'))['total'] or 0
        context['total_class_payment'] = total_class_payment

        # Add Breadcrumbs
        context['breadcrumbs'] = [
            ('/', 'Home'),
            (f'/homepage/schools/detail/{classe.ecole.pk}/', 'School Details'),
            ('', 'Class Details')
        ]

        return context


@method_decorator(login_required, name='dispatch')
class ClasseUpdateView(UpdateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the page identifier for this view
        context['page_identifier'] = 'S18'  # Example page identifier
        return context

    def get_success_url(self):
        return reverse_lazy('classe_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ClasseDeleteView(DeleteView):
    model = Classe
    template_name = 'scuelo/classe/classe_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the page identifier for this view
        context['page_identifier'] = 'S19'  # Example page identifier
        return context

    def get_success_url(self):
        return reverse_lazy('school_detail', kwargs={'pk': self.object.ecole.pk})


# =======================
# 4. Payment Management
# =======================
@csrf_exempt
@login_required
def add_payment(request, pk):
    student = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = PaiementPerStudentForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.inscription = Inscription.objects.filter(eleve=student).last()

            # Ensure the causal is set from the selected tariff
            if paiement.tarif:
                paiement.causal = paiement.tarif.causal
            else:
                # Handle the case where tarif is not set
                paiement.causal = "Unknown"

            paiement.save()

            # Log the payment
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Added Payment",
                old_value="",
                new_value=f"{paiement.causal} - {paiement.montant} - {paiement.note} - {paiement.date_paye}"
            )
            
            # Redirect to the student's detail page after successful payment
            return redirect('student_detail', pk=student.pk)
    else:
        form = PaiementPerStudentForm()

    return render(request, 'scuelo/paiements/add_payment.html', {'form': form, 'student': student ,
                                                                 'page_identifier': 'S07'})
@login_required
def update_paiement(request, pk):
    paiement = get_object_or_404(Mouvement, pk=pk)
    student = paiement.inscription.eleve
    if request.method == 'POST':
        form = PaiementPerStudentForm(request.POST, instance=paiement)
        if form.is_valid():
            form.save()
            # Log the update
            StudentLog.objects.create(
                student=student,
                user=request.user,
                action="Updated Payment",
                old_value=f"{paiement.causal} - {paiement.montant} - {paiement.note} - {paiement.date_paye}",
                new_value=f"{paiement.causal} - {form.cleaned_data['montant']} - {form.cleaned_data['note']} - {form.cleaned_data['date_paye']}"
            )
            return redirect('student_detail', pk=student.pk)
    else:
        form = PaiementPerStudentForm(instance=paiement)

    return render(request, 'scuelo/paiements/updatepaiment.html',
                  {'form': form, 'student': student ,
                                                                   'page_identifier': 'S07'})
@method_decorator(login_required, name='dispatch')
class UniformPaymentListView(ListView):
    model = Mouvement
    template_name = 'scuelo/uniforms/uniform_payments.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return Mouvement.objects.filter(causal='TEN').select_related('inscription__classe', 'inscription__eleve')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = self.get_queryset()

        # Group payments by class
        classes = {}
        total_uniforms_across_classes = 0

        for payment in payments:
            classe = payment.inscription.classe.nom
            student = payment.inscription.eleve
            school_type = payment.inscription.classe.type.type_ecole  # Assuming you have this attribute for school type
            cs_py = student.cs_py  # Assuming 'cs_py' contains 'CS' for Caisse Scolaire

            if classe not in classes:
                classes[classe] = {
                    'students': {},
                    'total_uniforms': 0,
                    'total_amount': 0
                }

            if student not in classes[classe]['students']:
                classes[classe]['students'][student] = {
                    'nom': student.nom,
                    'prenom': student.prenom,
                    'uniform_count': 0,
                    'total_amount': 0,
                }

            # Determine uniform count based on payment amount, school type, and CS status
            uniform_count = 0
            if cs_py == 'CS':
                # For students with 'CS' status
                if school_type == 'P' and payment.montant == 2250:
                    uniform_count = 1
                elif school_type == 'M' and payment.montant == 2000:
                    uniform_count = 1
            else:
                # For other students without 'CS' status
                if school_type in ['P', 'S', 'L']:  # Primaire, Secondaire, Lycée
                    if payment.montant == 4500:
                        uniform_count = 2
                    elif payment.montant == 2250:
                        uniform_count = 1
                elif school_type == 'M':  # Maternelle
                    if payment.montant == 4000:
                        uniform_count = 2
                    elif payment.montant == 2000:
                        uniform_count = 1

            # Update student and class data
            classes[classe]['students'][student]['uniform_count'] += uniform_count
            classes[classe]['students'][student]['total_amount'] += payment.montant
            classes[classe]['total_uniforms'] += uniform_count
            classes[classe]['total_amount'] += payment.montant
            total_uniforms_across_classes += uniform_count

        # Pass the context to the template
        context['classes'] = classes  
        context['page_identifier'] = 'S20'  # Example page identifier
        context['total_uniforms'] = total_uniforms_across_classes
        return context
    
def student_search(request):
    """API endpoint for filtering students by name."""
    term = request.GET.get('q', '')
    students = Eleve.objects.filter(nom__icontains=term)[:10]  # Limits results for performance
    student_list = [{'id': student.id, 'text': f"{student.nom} {student.prenom}"} for student in students]
    return JsonResponse({'results': student_list})    

class UniformReservationListView(ListView):
    model = UniformReservation
    template_name = 'scuelo/reservations/uniform_reservation_list.html'
    context_object_name = 'reservations'

class UniformReservationCreateView(CreateView):
    model = UniformReservation
    form_class = UniformReservationForm
    template_name = 'scuelo/reservations/uniform_reservation_form.html'
    success_url = reverse_lazy('uniform-reservation-list')

    def get_initial(self):
        initial = super().get_initial()
        student = get_object_or_404(Eleve, pk=self.kwargs['student_pk'])
        initial.update({'student': student})
        return initial

    def form_valid(self, form):
        # Automatically set the current school year if not set
        if not form.instance.school_year:
            current_school_year = AnneeScolaire.objects.filter(actuel=True).first()
            if not current_school_year:
                raise Exception("No current school year is defined.")
            form.instance.school_year = current_school_year
        return super().form_valid(form)



class UniformReservationUpdateView(UpdateView):
    model = UniformReservation
    form_class = UniformReservationForm
    template_name = 'scuelo/reservations/uniform_reservation_form.html'
    success_url = reverse_lazy('uniform-reservation-list')

class UniformReservationDeleteView(DeleteView):
    model = UniformReservation
    template_name = 'scuelo/reservations/uniform_reservation_confirm_delete.html'
    success_url = reverse_lazy('uniform-reservation-list')    
    
    
    
    
@login_required
def cash_flow_report(request):
    # Get all movements for the current year
    current_date = now()
    movements = Mouvement.objects.filter(date_paye__year=current_date.year)
    
    # Calculate key metrics
    total_revenue = movements.filter(type='R').aggregate(total=Sum('montant'))['total'] or 0
    total_expenses = movements.filter(type='D').aggregate(total=Sum('montant'))['total'] or 0
    net_cash_flow = total_revenue - total_expenses
    
    # Group by months for trend analysis
    monthly_data = movements.values('date_paye__month').annotate(
        total_inflow=Sum('montant', filter=models.Q(type='R')),
        total_outflow=Sum('montant', filter=models.Q(type='D'))
    ).order_by('date_paye__month')
    
    # Create Monthly Cash Flow Chart
    months = [month['date_paye__month'] for month in monthly_data]
    inflow = [month['total_inflow'] or 0 for month in monthly_data]
    outflow = [month['total_outflow'] or 0 for month in monthly_data]

    plt.figure(figsize=(10, 6))
    plt.plot(months, inflow, marker='o', label='Inflow')
    plt.plot(months, outflow, marker='o', label='Outflow')
    plt.title('Monthly Cash Flow')
    plt.xlabel('Month')
    plt.ylabel('Amount')
    plt.legend()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    monthly_cash_flow_chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    # Income vs Expenses Pie Chart
    labels = ['Revenue', 'Expenses']
    sizes = [total_revenue, total_expenses]
    colors = ['#28a745', '#dc3545']

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Revenue vs Expenses')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    income_vs_expenses_chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    context = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_cash_flow': net_cash_flow,
        'monthly_cash_flow_chart': monthly_cash_flow_chart,
        'income_vs_expenses_chart': income_vs_expenses_chart,
        'page_identifier': 'S08'
    }
    return render(request, 'scuelo/cash/cash_flow_report.html', context)



@login_required
def manage_tarifs(request, pk):
    # Fetch the class and current school year
    classe = get_object_or_404(Classe, pk=pk)
    current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

        # Fetch the students in this class for the current academic year
    inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire)
        # Count total students
    student_count = inscriptions.count()
        # Count students who are both PY and CONF
    confirmed_py_count = inscriptions.filter(
        eleve__cs_py="P",  # PY students
        eleve__condition_eleve="CONF"  # CONF students
    ).count()

    # Count CS students
    cs_students_count = inscriptions.filter(eleve__cs_py="C").count()

    # Count PY students
    py_students_count = inscriptions.filter(eleve__cs_py="P").count()

    # Count other students (students who are neither CS nor PY)
    other_students_count = student_count - (cs_students_count + py_students_count)


    # Fetch confirmed PY students for the class
    confirmed_py_count = Inscription.objects.filter(
        classe=classe,
        annee_scolaire=current_annee_scolaire,
        eleve__condition_eleve="CONF",
        eleve__cs_py="P"
    ).count()

    # Fetch all tariffs for the class in the current school year
    tarifs = Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire)

    # Calculate cumulative amounts for each tranche (using 'causal' instead of 'type_frais')
    # Calculate cumulative sums for each tranche
    tranche_data = {
        'first_tranche': tarifs.filter(causal='SCO1').aggregate(total=Sum('montant'))['total'] or 0,
        'second_tranche': (tarifs.filter(causal='SCO1').aggregate(total=Sum('montant'))['total'] or 0) +
                        (tarifs.filter(causal='SCO2').aggregate(total=Sum('montant'))['total'] or 0),
        'third_tranche': (tarifs.filter(causal='SCO1').aggregate(total=Sum('montant'))['total'] or 0) +
                        (tarifs.filter(causal='SCO2').aggregate(total=Sum('montant'))['total'] or 0) +
                        (tarifs.filter(causal='SCO3').aggregate(total=Sum('montant'))['total'] or 0),
    }


    # Calculate progressive payments per student
    progress_per_eleve = (
                          tranche_data['third_tranche'])

    # Calculate the expected total payment for the class at each tranche
    expected_payment = {
        'first_tranche': tranche_data['first_tranche'] * confirmed_py_count,
        'second_tranche': tranche_data['second_tranche'] * confirmed_py_count,
        'third_tranche': tranche_data['third_tranche'] * confirmed_py_count
    }

    # Calculate total actual payments
    total_actual_payments = Mouvement.objects.filter(
        inscription__classe=classe,
        inscription__annee_scolaire=current_annee_scolaire
    ).aggregate(total=Sum('montant'))['total'] or 0

       # Fetch count of students (PY, CS, and others)
    student_count = Inscription.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire).count()
    py_students_count = Inscription.objects.filter(
        classe=classe, annee_scolaire=current_annee_scolaire, eleve__cs_py="P"
    ).count()
      # Filter and count students who are PY and CONF
    py_conf_students_count = Inscription.objects.filter(
        classe=classe,
        annee_scolaire=current_annee_scolaire,
        eleve__cs_py="P",  # Filtering PY students
        eleve__condition_eleve="CONF"  # Filtering CONF students
    ).count()

    cs_students_count = Inscription.objects.filter(
        classe=classe, annee_scolaire=current_annee_scolaire, eleve__cs_py="C"
    ).count()
    other_students_count = student_count - py_students_count - cs_students_count
    cs_students_count = inscriptions.filter(eleve__cs_py="C").count()
    return render(request, 'scuelo/tarif/tarif_list.html', {
        'classe': classe,
        'tarifs': tarifs,
        'progress_per_eleve': progress_per_eleve,
        'tranche_data': tranche_data,
        #'py_conf_students_count':  py_conf_students_count ,
        'student_count': student_count,
        'confirmed_py_count': confirmed_py_count,
        'expected_payment': expected_payment,
        'py_students_count': py_students_count,
        'cs_students_count': cs_students_count,
        'other_students_count': other_students_count,
        'total_actual_payments': total_actual_payments,  
        'page_identifier': 'S09'
        
    })


@login_required
def add_tarif(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

    if request.method == 'POST':
        form = TarifForm(request.POST)
        if form.is_valid():
            tarif = form.save(commit=False)
            tarif.classe = classe
            tarif.annee_scolaire = current_annee_scolaire
            tarif.save()
            return redirect('manage_tarifs', pk=classe.pk)
    else:
        form = TarifForm()

    return render(request, 'scuelo/tarif/tarif_form.html', {'form': form, 'classe': classe})

@login_required
def update_tarif(request, pk):
    tarif = get_object_or_404(Tarif, pk=pk)
    classe = tarif.classe

    if request.method == 'POST':
        form = TarifForm(request.POST, instance=tarif)
        if form.is_valid():
            form.save()
            return redirect('manage_tarifs', pk=classe.pk)
    else:
        form = TarifForm(instance=tarif)

    return render(request, 'scuelo/tarif/tarif_form.html', {'form': form, 'classe': classe})

@login_required
def delete_tarif(request, pk):
    tarif = get_object_or_404(Tarif, pk=pk)
    classe = tarif.classe

    if request.method == 'POST':  # If the user confirms deletion
        if 'confirm' in request.POST:
            tarif.delete()
            return redirect('manage_tarifs', pk=classe.pk)  # Redirect after deletion
        else:
            return redirect('manage_tarifs', pk=classe.pk)  # Redirect if the user cancels

    return render(request, 'scuelo/tarif/tarif_confirm_delete.html', {'tarif': tarif})


@login_required
def export_accounting_report(request):
    # Exporting the accounting report to CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="accounting_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Period', 'Total Income'])

    grouped_income = Mouvement.objects.filter(
        Q(type='R'),
        date_paye__gte=start_of_period
    ).annotate(period=Case(
        When(date_paye__lt=mid_of_period, then=Value('1st-15th')),
        default=Value('16th-end')
    )).values('period').annotate(total=Sum('montant')).order_by('period')

    for row in grouped_income:
        writer.writerow([row['period'], row['total']])

    return response


@login_required
def mouvement_list(request):
    search_query = request.GET.get('search', '')

    # Fetch all movements ordered by payment date
    movements = Mouvement.objects.all().order_by('date_paye')

    # Apply search filters if search_query is provided
    if search_query:
        movements = movements.filter(
            Q(causal__icontains=search_query) | 
            Q(note__icontains=search_query) |
            Q(inscription__eleve__nom__icontains=search_query) |
            Q(inscription__eleve__prenom__icontains=search_query)
        )

    # Initialize progressive total
    progressive_total = 0

    # Create a list to store processed movements with extra information
    processed_movements = []

    # Loop over movements to calculate the progressive total and build description
    for mouvement in movements:
        # If the causal is missing but linked to a tarif, set it
        if mouvement.tarif and not mouvement.causal:
            mouvement.causal = mouvement.tarif.causal
            mouvement.save()

        # Define the type based on the causal:
        # All causals related to school fees (CAN, SCO1, SCO2, SCO3, TEN) are considered income (Recette)
        if mouvement.causal in ['INS', 'SCO1', 'SCO2', 'SCO3', 'TEN', 'CAN']:  # Add any other causals as needed
            mouvement.type = 'R'  # Recette (Inflow)
        else:
            mouvement.type = 'R'  # Dépense (Outflow)

        # Adjust the progressive total based on the movement type
        if mouvement.type == 'R':
            progressive_total += mouvement.montant  # Add inflows
            entry = mouvement.montant
            exit = ''
        elif mouvement.type == 'D':
            progressive_total -= mouvement.montant  # Subtract outflows
            entry = ''
            exit = mouvement.montant

        # Create a dynamic description combining student's full name, school name, and class
        if mouvement.inscription and mouvement.inscription.classe:
            student_name = f"{mouvement.inscription.eleve.nom} {mouvement.inscription.eleve.prenom}"
            school_name = mouvement.inscription.classe.ecole.nom if mouvement.inscription.classe.ecole else "Unknown School"
            class_name = mouvement.inscription.classe.nom
            description = f"{student_name} - {school_name} - {class_name}"
        else:
            description = f"Unknown Student - No Class Info"

        # Append processed data to the list
        processed_movements.append({
            'date': mouvement.date_paye,
            'description': description,
            'entry': entry,
            'exit': exit,
            'progressive_total': progressive_total
        })

    return render(request, 'scuelo/mouvement/mouvement_list.html', {
        'movements': processed_movements,
        'search_query': search_query,
        'page_identifier': 'S11'
    })

@login_required
def accounting_c_sco_report(request, period=None):
    search_query = request.GET.get('search', '')

    # Fetch all movements ordered by payment date
    movements = Mouvement.objects.all().order_by('date_paye')

    # Apply search filters if search_query is provided
    if search_query:
        movements = movements.filter(
            Q(causal__icontains=search_query) | 
            Q(note__icontains=search_query) |
            Q(inscription__eleve__nom__icontains=search_query) |
            Q(inscription__eleve__prenom__icontains=search_query)
        )

    # Initialize progressive total
    progressive_total = 0
    processed_movements = []

    # Group data by period if specified
    if period == 'weekly':
        # Define the start of the current week
        current_date = timezone.now().date()
        start_of_week = current_date - timedelta(days=current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Group movements by week
        movements = movements.filter(date_paye__range=[start_of_week, end_of_week])
        grouping_key = 'WEEKLY'

    elif period == 'bi-monthly':
        # Define ranges for 1st to 15th and 16th to end of the month
        current_date = timezone.now().date()
        if current_date.day <= 15:
            start_of_period = current_date.replace(day=1)
            end_of_period = current_date.replace(day=15)
        else:
            start_of_period = current_date.replace(day=16)
            last_day = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            end_of_period = last_day

        # Group movements within the period range
        movements = movements.filter(date_paye__range=[start_of_period, end_of_period])
        grouping_key = 'BI-MONTHLY'

    else:
        grouping_key = 'ALL'

    # Loop over movements to calculate the progressive total and build description
    for mouvement in movements:
        # Ensure the correct type is assigned (R for inflows, D for outflows)
        if mouvement.causal in ['INS', 'SCO1', 'SCO2', 'SCO3', 'TEN', 'CAN']:
            mouvement.type = 'R'  # Recette (Inflow)
        else:
            mouvement.type = 'D'  # Dépense (Outflow)

        # Adjust the progressive total based on the movement type
        if mouvement.type == 'R':
            progressive_total += mouvement.montant  # Add inflows
            entry = mouvement.montant
            exit = ''
        elif mouvement.type == 'D':
            progressive_total -= mouvement.montant  # Subtract outflows
            entry = ''
            exit = mouvement.montant

        # Create a dynamic description combining student's full name, school name, and class
        if mouvement.inscription and mouvement.inscription.classe:
            student_name = f"{mouvement.inscription.eleve.nom} {mouvement.inscription.eleve.prenom}"
            school_name = mouvement.inscription.classe.ecole.nom if mouvement.inscription.classe.ecole else "Unknown School"
            class_name = mouvement.inscription.classe.nom
            description = f"{student_name} - {school_name} - {class_name}"
        else:
            description = "Unknown Student - No Class Info"

        # Append processed data to the list
        processed_movements.append({
            'date': mouvement.date_paye,
            'description': description,
            'entry': entry,
            'exit': exit,
            'progressive_total': progressive_total,
            'grouping': grouping_key
        })

    return render(request, 'scuelo/mouvement/accounting_report.html', {
        'movements': processed_movements,
        'search_query': search_query,
        'page_identifier': 'SCO Accounting',
        'grouping_key': grouping_key
    })



@login_required
def add_mouvement(request):
    if request.method == 'POST':
        form = MouvementForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            # Set the type to 'R' (Income) if causal is one of the income categories
            if mouvement.causal in ['INS', 'SCO1', 'SCO2', 'SCO3', 'TEN', 'CAN']:
                mouvement.type = 'R'  # Income
            else:
                mouvement.type = 'D'  # Expense
            mouvement.save()
            return redirect('mouvement_list')
    else:
        form = MouvementForm()

    return render(request, 'scuelo/mouvement/add_mouvement.html', {'form': form , 'page_identifier': 'S12'})
        

@login_required
def update_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        form = MouvementForm(request.POST, instance=mouvement)
        if form.is_valid():
            form.save()
            return redirect('mouvement_list')
    else:
        form = MouvementForm(instance=mouvement)
    return render(request, 'scuelo/mouvement/update_mouvement.html', {'form': form,
                                                                      'mouvement': mouvement , 'page_identifier': 'S13'})

@login_required
def delete_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        mouvement.delete()
        return redirect('mouvement_list')
    return render(request, 'scuelo/mouvement/delete_mouvement.html', {'mouvement': mouvement ,
                                                                      'page_identifier': 'S14' })



@login_required
def late_payment_report(request):
    data = {}
    schools = Ecole.objects.all()

    # Get the current school year
    current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

    for school in schools:
        classes = Classe.objects.filter(ecole=school)
        class_data = {}

        for classe in classes:
            # Get all students who are 'PY' in the current class
            students = Eleve.objects.filter(inscription__classe=classe, cs_py='PY')
            student_data = []
            total_class_remaining = 0  # Track the total rest to be paid for the class

            for student in students:
                payments = Mouvement.objects.filter(inscription__eleve=student)
                sco_paid = payments.aggregate(Sum('montant'))['montant__sum'] or 0
                # Calculate CAN paid specifically
                can_paid = payments.filter(causal='CAN').aggregate(total=Sum('montant'))['total'] or 0

                # Fetch all tariffs for the class in the current school year
                tarifs = Tarif.objects.filter(
                    classe=classe, 
                    annee_scolaire=current_annee_scolaire
                )

                # Calculate the SCO exigible as the sum of SCO1, SCO2, and SCO3 for the current school year
                sco_exigible = tarifs.filter(causal__in=['SCO1', 'SCO2', 'SCO3']).aggregate(total=Sum('montant'))['total'] or 0

                # Calculate the CAN exigible separately
                can_exigible = tarifs.filter(causal='CAN').aggregate(total=Sum('montant'))['total'] or 0

                # Correct difference calculations
                diff_sco = sco_exigible - sco_paid  # Remaining SCO amount to be paid
                diff_can = can_exigible - can_paid  # Remaining CAN amount to be paid
                retards = diff_sco + diff_can

                # Accumulate the total remaining for the class
                total_class_remaining += retards

                # Only include students who have retards (not fully paid)
                if retards > 0:  # Adjusted condition to show students with outstanding amounts
                    percentage_paid = int(
                        100 * (sco_paid + can_paid) / (sco_exigible + can_exigible)
                    ) if (sco_exigible + can_exigible) > 0 else 0

                    student_data.append({
                        'id': student.id,
                        'nom': student.nom,
                        'prenom': student.prenom,
                        'sex': student.sex,
                        'cs_py': student.cs_py,
                        'sco_paid': sco_paid,
                        'sco_exigible': sco_exigible,
                        'diff_sco': diff_sco,  # Remaining SCO amount
                        'can_paid': can_paid,
                        'can_exigible': can_exigible,
                        'diff_can': diff_can,  # Remaining CAN amount
                        'retards': retards,
                        'percentage_paid': percentage_paid,
                        'note': student.note_eleve,
                    })

            # Only add the class if there are students with late payments
            if student_data:
                class_data[classe.nom] = {
                    'students': student_data,
                    'total_class_remaining': total_class_remaining  # Add total remaining amount for the class
                }

        # Only add the school if there are classes with students having late payments
        if class_data:
            data[school.nom] = class_data

    return render(request, 'scuelo/late_payment.html', {'data': data})


# =======================
# 5. School Management
# =======================
@method_decorator(login_required, name='dispatch')
class SchoolManagementView(TemplateView):
    template_name = 'scuelo/school/school_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schools'] = Ecole.objects.annotate(num_students=Count('classe__inscription__eleve', distinct=True))
        context['form'] = EcoleCreateForm()
        context['page_identifier'] = 'S25'  # Add page identifier
        return context

@method_decorator(login_required, name='dispatch')
class SchoolCreateView(CreateView):
    model = Ecole
    form_class = EcoleCreateForm
    template_name = 'scuelo/school_create.html'
    success_url = reverse_lazy('school_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_identifier'] = 'S26'  # Add page identifier
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"message": "Success"})
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(form.errors, status=400)
        return response

@method_decorator(login_required, name='dispatch')
class SchoolUpdateView(UpdateView):
    model = Ecole
    form_class = EcoleCreateForm
    template_name = 'scuelo/school/school_update.html'
    success_url = reverse_lazy('school_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_identifier'] = 'S27'  # Add page identifier
        return context


@method_decorator(login_required, name='dispatch')
class SchoolDeleteView(DeleteView):
    model = Ecole
    template_name = 'scuelo/school/school_confirm_delete.html'
    success_url = reverse_lazy('school_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_identifier'] = 'S28'  # Add page identifier
        return context

    def delete(self, request, *args, **kwargs):
        # Optional: Add any pre-deletion logic here
        return super().delete(request, *args, **kwargs)

    
@method_decorator(login_required, name='dispatch')
class SchoolDetailView(DetailView):
    model = Ecole
    template_name = 'scuelo/school/school_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Eleve.objects.filter(inscription__classe__ecole=self.object).distinct()
        context['classe_form'] = ClasseCreateForm()
        context['page_identifier'] = 'S29'  # Add unique page identifier
        return context

@login_required
def load_classes(request):
    school_id = request.GET.get('school_id')
    classes = Classe.objects.filter(ecole_id=school_id).order_by('nom')
    return JsonResponse(list(classes.values('id', 'nom')), safe=False)


# =======================
# 6. Financial Management
# =======================
def print_receipt(request, mouvement_id):
    mouvement = get_object_or_404(Mouvement, id=mouvement_id)
    context = {
        'mouvement': mouvement,
        'receipt_number': f'REC-{mouvement.id:05d}'  # Example receipt number format
    }
    html_string = render(request, 'scuelo/receipt_template.html', context).content.decode('utf-8')
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="receipt_{mouvement.id}.pdf"'
    return response
