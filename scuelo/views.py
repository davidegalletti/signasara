# Authentication
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import UpdateView, DeleteView
from django.views.generic import DetailView, ListView, CreateView, TemplateView
from django.db.models import Q, Sum, Prefetch, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseRedirect
from weasyprint import HTML
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.db.models import Sum, Q , F
from datetime import timedelta, datetime
import csv
import io

from django.http import HttpResponse

from django.utils import timezone
from .models import Eleve, Inscription, Mouvement, StudentLog
from .forms import PaiementPerStudentForm

from django.db.models import Sum
import base64
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum, Case, When, Value
from django.db.models.functions import TruncDay
# Models and Forms
from django.utils.timezone import now
from .forms import (
    PaiementPerStudentForm, EleveUpdateForm, MouvementForm,
    EleveCreateForm, EcoleCreateForm, ClasseCreateForm,
    TarifForm, ClassUpgradeForm, SchoolChangeForm
)
from scuelo.models import (
    Eleve, Classe, Inscription, StudentLog,
    AnneeScolaire, Mouvement, Ecole, Tarif
)
from django.db.models import Sum, Q
from datetime import timedelta, datetime
import csv
from django.http import HttpResponse

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
@login_required
def home(request):
    schools = Ecole.objects.all()
    data = {}
    for school in schools:
        classes = Classe.objects.filter(ecole=school)
        class_data = []
        for classe in classes:
            if Inscription.objects.filter(classe=classe).exists():
                class_data.append(classe)
        if class_data:
            data[school] = class_data
    breadcrumbs = [('/', 'Home')]  # Update breadcrumbs as needed
    return render(request, 'scuelo/home.html', {'data': data, 'breadcrumbs': breadcrumbs})

from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from scuelo.models import Classe, AnneeScolaire, Inscription, Mouvement, Tarif

@login_required
def class_detail(request, pk):
    # Get the class based on the provided primary key (pk)
    classe = get_object_or_404(Classe, pk=pk)

    # Get all academic years to display in the selection dropdown
    all_annee_scolaires = AnneeScolaire.objects.all()

    # Get the selected academic year, default to the current year if none is selected
    selected_annee_scolaire_id = request.GET.get('annee_scolaire', None)
    if selected_annee_scolaire_id:
        selected_annee_scolaire = AnneeScolaire.objects.get(pk=selected_annee_scolaire_id)
    else:
        # Default to the current academic year if none is selected
        selected_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

    # Get students registered in this class during the selected academic year
    inscriptions = Inscription.objects.filter(classe=classe, annee_scolaire=selected_annee_scolaire)
    students = [inscription.eleve for inscription in inscriptions]

    # Calculate total payments for each student
    for student in students:
        total_payment = Mouvement.objects.filter(inscription__eleve=student).aggregate(total=Sum('montant'))['total'] or 0
        student.total_payment = total_payment

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
        'selected_annee_scolaire': selected_annee_scolaire  # Pass the selected academic year
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
        breadcrumbs = [
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
    
    return render(request, 'scuelo/students/studentupdate.html', {'form': form, 'student': student})

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

    return render(request, 'scuelo/classe/class_upgrade.html', {'form': form, 'student': student})

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

    return render(request, 'scuelo/school/change_school.html', {'form': form, 'student': student})

@login_required
def offsite_students(request):
    # Get the current school year
    current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

    # Fetch offsite students by filtering on Inscription and related models, including students with null `annee_inscr`
    inscriptions = Inscription.objects.filter(
        ~Q(classe__ecole__nom__iexact="Bisongo du coeur"),
        annee_scolaire=current_annee_scolaire
    ).select_related('eleve', 'classe__ecole')

    # Get the list of offsite students from the inscriptions, including those with null `annee_inscr`
    offsite_students = []
    for inscription in inscriptions:
        student = inscription.eleve
        student.total_paiements = Mouvement.objects.filter(inscription=inscription).aggregate(total=Sum('montant'))['total'] or 0
        student.school_name = inscription.classe.ecole.nom
        offsite_students.append(student)

    # Add a filter to include students even if `annee_inscr` is null
    null_annee_inscr_students = [student for student in offsite_students if student.annee_inscr is None]

    context = {
        'offsite_students': offsite_students,
        'null_annee_inscr_students': null_annee_inscr_students,
        'current_annee_scolaire': current_annee_scolaire
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

@method_decorator(login_required, name='dispatch')
class ClasseDetailView(DetailView):
    model = Classe
    template_name = 'scuelo/classe/classe_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classe = self.get_object()
        context['students'] = Eleve.objects.filter(inscription__classe=classe)
        context['breadcrumbs'] = [('/', 'Home'), 
                                  (f'/homepage/schools/detail/{classe.ecole.pk}/', 'School Details'), 
                                  ('', 'Class Details')]
        return context

@method_decorator(login_required, name='dispatch')
class ClasseUpdateView(UpdateView):
    model = Classe
    form_class = ClasseCreateForm
    template_name = 'scuelo/classe/classe_update.html'

    def get_success_url(self):
        return reverse_lazy('classe_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ClasseDeleteView(DeleteView):
    model = Classe
    template_name = 'scuelo/classe/classe_confirm_delete.html'

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

    return render(request, 'scuelo/paiements/add_payment.html', {'form': form, 'student': student})
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

    return render(request, 'scuelo/paiements/updatepaiment.html', {'form': form, 'student': student})
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
        context['total_uniforms'] = total_uniforms_across_classes
        return context

@method_decorator(login_required, name='dispatch')
class UniformPaymentCreateView(CreateView):
    model = Mouvement
    form_class = MouvementForm
    template_name = 'payment_form.html'
    success_url = reverse_lazy('uniform_payments')

    def form_valid(self, form):
        form.instance.causal = 'TEN'
        return super().form_valid(form)


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
    }
    return render(request, 'scuelo/cash/cash_flow_report.html', context)

@login_required
def manage_tarifs(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    current_annee_scolaire = AnneeScolaire.objects.get(actuel=True)

    # Get the number of students in the class
    student_count = Inscription.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire).count()

    # Get the number of students that are both CONF and PY
    confirmed_py_count = Inscription.objects.filter(
        classe=classe,
        annee_scolaire=current_annee_scolaire,
        eleve__condition_eleve="CONF",  # Filtering students that are CONF
        eleve__cs_py="P"  # Filtering students that are PY
    ).count()

    # Modelformset for Tarif model
    TarifFormset = modelformset_factory(Tarif, form=TarifForm, extra=3, can_delete=True)

    if request.method == 'POST':
        formset = TarifFormset(request.POST, queryset=Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire))

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.classe = classe
                instance.annee_scolaire = current_annee_scolaire
                instance.save()

            # Delete instances marked for deletion
            for obj in formset.deleted_objects:
                obj.delete()

            return redirect('class_detail', pk=classe.pk)
        else:
            print("Formset errors: ", formset.errors)
    else:
        formset = TarifFormset(queryset=Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire))

    # Calculate cumulative amounts for each type
    cumulative_data = Tarif.objects.filter(classe=classe, annee_scolaire=current_annee_scolaire).aggregate(
        total_inscription=Sum('montant', filter=Q(causal='INS')),
        total_sco1=Sum('montant', filter=Q(causal='SCO1')),
        total_sco2=Sum('montant', filter=Q(causal='SCO2')),
        total_sco3=Sum('montant', filter=Q(causal='SCO3')),
    )

    # Calculate cumulative progress per eleve and tranche
    progress_per_eleve = sum([
        cumulative_data.get('total_inscription') or 0,
        cumulative_data.get('total_sco1') or 0,
        cumulative_data.get('total_sco2') or 0,
        cumulative_data.get('total_sco3') or 0
    ])

    tranche_data = {
        'first_tranche': cumulative_data.get('total_sco1') or 0,
        'second_tranche': (cumulative_data.get('total_sco1') or 0) + (cumulative_data.get('total_sco2') or 0),
        'third_tranche': (cumulative_data.get('total_sco1') or 0) + (cumulative_data.get('total_sco2') or 0) + (cumulative_data.get('total_sco3') or 0)
    }

    # Calculate the expected payment for the class at each tranche (confirmed PY students)
    expected_payment = {
        'first_tranche': tranche_data['first_tranche'] * confirmed_py_count,
        'second_tranche': tranche_data['second_tranche'] * confirmed_py_count,
        'third_tranche': tranche_data['third_tranche'] * confirmed_py_count
    }

    # Calculate total actual payments (optional if you want to display actual payments)
    total_actual_payments = Mouvement.objects.filter(inscription__classe=classe, inscription__annee_scolaire=current_annee_scolaire).aggregate(total=Sum('montant'))['total'] or 0

    # Get the expected payments by the date of the late SCO1
    latest_sco1_date = Tarif.objects.filter(causal='SCO1').order_by('-date_expiration').first()
    if latest_sco1_date:
        expected_payment['first_tranche'] = tranche_data['first_tranche'] * confirmed_py_count

     # Count CS students
    cs_students_count = Inscription.objects.filter(
        classe=classe,
        annee_scolaire=current_annee_scolaire,
        eleve__cs_py="C"  # Filtering CS students
    ).count()

    # Count PY students
    py_students_count = Inscription.objects.filter(
        classe=classe,
        annee_scolaire=current_annee_scolaire,
        eleve__cs_py="P"  # Filtering PY students
    ).count()

    # Count other students (students who are neither CS nor PY)
    other_students_count = student_count - (cs_students_count - py_students_count)
    
    return render(request, 'scuelo/tarif/tarif_list.html', {
        'classe': classe,
        'formset': formset,
        'progress_per_eleve': progress_per_eleve,
        'tranche_data': tranche_data,
        'student_count': student_count,  # Pass student count to template
        'confirmed_py_count': confirmed_py_count,  # Pass CONF PY count to template
        'expected_payment': expected_payment,
        'py_students_count':py_students_count ,
        'cs_students_count':cs_students_count,
        'other_students_count':other_students_count,
        'total_actual_payments': total_actual_payments  # Pass total actual payments to template
    })


class TarifCreateView(CreateView):
    model = Tarif
    form_class = TarifForm
    template_name = 'scuelo/paiements/tarif_form.html'

    def get_success_url(self):
        return reverse_lazy('manage_tarifs', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        classe = get_object_or_404(Classe, pk=self.kwargs['pk'])
        form.instance.classe = classe
        return super().form_valid(form)

# Update an existing tariff
@method_decorator(login_required, name='dispatch')
class TarifUpdateView(UpdateView):
    model = Tarif
    form_class = TarifForm
    template_name = 'tarifs/tarif_form.html'

    def get_success_url(self):
        return reverse_lazy('manage_tarifs', kwargs={'pk': self.object.classe.pk})
    
# Delete a tariff
@method_decorator(login_required, name='dispatch')
class TarifDeleteView(DeleteView):
    model = Tarif
    template_name = 'tarifs/tarif_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('manage_tarifs', kwargs={'pk': self.object.classe.pk})
    
@login_required
def accounting_report(request):
    # Grouping by period (e.g., 1st-15th and 16th-end)
    start_of_period = datetime.now().replace(day=1)  # Start of the month
    mid_of_period = datetime.now().replace(day=16)  # Mid of the month
    
    grouped_income = Mouvement.objects.filter(
        Q(type='R'),
        date_paye__gte=start_of_period
    ).annotate(period=Case(
        When(date_paye__lt=mid_of_period, then=Value('1st-15th')),
        default=Value('16th-end')
    )).values('period').annotate(total=Sum('montant')).order_by('period')

    return render(request, 'scuelo/cash/accounting_report.html', {'grouped_income': grouped_income})

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
    movements = Mouvement.objects.all().order_by('-date_paye')

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

    # Loop over movements to calculate the progressive total and build description
    for mouvement in movements:
        # If the causal is missing but linked to a tarif, set it
        if mouvement.tarif and not mouvement.causal:
            mouvement.causal = mouvement.tarif.causal
            mouvement.save()

        # Define the type based on the causal:
        # All causals related to "Scolarité" or "Classe" fees are considered "Recette" (Inflow)
        if mouvement.causal in ['INS', 'SCO1', 'SCO2', 'SCO3', 'TEN', 'CAN']:  # Add any other causals as needed
            mouvement.type = 'R'  # Recette (Inflow)
        else:
            mouvement.type = 'D'  # Dépense (Outflow)

        # Adjust the progressive total based on the movement type
        if mouvement.type == 'R':
            progressive_total += mouvement.montant  # Add inflows
        elif mouvement.type == 'D':
            progressive_total -= mouvement.montant  # Subtract outflows

        # Assign the computed progressive total as a dynamic attribute
        mouvement.progressive_total = progressive_total

        # Create a dynamic description combining student's full name, school name, and class
        if mouvement.inscription and mouvement.inscription.classe:
            student_name = f"{mouvement.inscription.eleve.nom} {mouvement.inscription.eleve.prenom}"
            school_name = mouvement.inscription.classe.ecole.nom if mouvement.inscription.classe.ecole else "Unknown School"
            class_name = mouvement.inscription.classe.nom
            mouvement.description = f"{student_name} - {school_name} - {class_name}"
        else:
            mouvement.description = f"Unknown Student - No Class Info"
        
        # Save movement after adding the description and calculating the progressive total
        mouvement.save()

    return render(request, 'scuelo/mouvement/mouvement_list.html', {
        'movements': movements,
        'search_query': search_query,
    })
@login_required
def add_mouvement(request):
    if request.method == 'POST':
        form = MouvementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('mouvement_list')
    else:
        form = MouvementForm()
    return render(request, 'scuelo/mouvement/add_mouvement.html', {'form': form})
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
    return render(request, 'scuelo/mouvement/update_mouvement.html', {'form': form, 'mouvement': mouvement})

@login_required
def delete_mouvement(request, pk):
    mouvement = get_object_or_404(Mouvement, pk=pk)
    if request.method == 'POST':
        mouvement.delete()
        return redirect('mouvement_list')
    return render(request, 'scuelo/mouvement/delete_mouvement.html', {'mouvement': mouvement})



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
        return context

@method_decorator(login_required, name='dispatch')
class SchoolCreateView(CreateView):
    model = Ecole
    form_class = EcoleCreateForm
    template_name = 'scuelo/school_create.html'
    success_url = reverse_lazy('student_management')

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
    success_url = reverse_lazy('student_management')

@method_decorator(login_required, name='dispatch')
class SchoolDeleteView(DeleteView):
    model = Ecole
    template_name = 'scuelo/school/school_confirm_delete.html'
    success_url = reverse_lazy('school_management')

    def delete(self, request, *args, **kwargs):
        """
        Override the delete method to add any additional logic if needed,
        like checking if the school has any related objects that should
        also be deleted or should prevent deletion.
        """
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
