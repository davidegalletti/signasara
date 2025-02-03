from django.urls import path
from . import views
from .views import (
    StudentListView, StudentCreateView, SchoolManagementView, SchoolCreateView,
    SchoolUpdateView, SchoolDeleteView, SchoolDetailView,ClassCreateView ,
    ClasseDetailView, ClasseUpdateView, ClasseDeleteView ,ClasseInformation
     , print_receipt  
      , login_view , SchoolYearManagementView ,AddSchoolYearView , DeleteSchoolYearView , EditSchoolYearView ,
  
    
)

urlpatterns = [
    path('', views.home, name='home'),
    path('class/<int:pk>/', views.class_detail, name='class_detail'),
    path('login/', login_view, name='login'),
    path('select-school-year/', views.select_school_year, name='select_school_year'),
    
    path('student_update/<int:pk>/', views.student_update, name='student_update'),  # Add this line
    path('logout/', views.logout_view, name='logout'),
    path('annee_scolaire/manage/', views.SchoolYearManagementView.as_view(), name='annee_scolaire_manage'),
    path('annee_scolaire/add/', views.AddSchoolYearView.as_view(), name='add_school_year'),
    path('annee_scolaire/edit/<int:pk>/', views.EditSchoolYearView.as_view(), name='edit_school_year'),
    path('annee_scolaire/delete/<int:pk>/', DeleteSchoolYearView.as_view(), name='delete_school_year'),

    path('offsite_students/', views.offsite_students, name='offsite_students'),
    path('directly_managed_students/', StudentListView.as_view(), name='directly_managed_students'),
    path('new_student/', StudentCreateView.as_view(), name='new_student'),
    path('change_school/<int:pk>/', views.change_school, name='change_school'),

    path('class_upgrade/<int:pk>/', views.class_upgrade, name='class_upgrade'),
    path('school_management/', SchoolManagementView.as_view(), name='school_management'),
    path('schools/create/', SchoolCreateView.as_view(), name='school_create'),
    path('schools/update/<int:pk>/', SchoolUpdateView.as_view(), name='school_update'),
    path('schools/delete/<int:pk>/', SchoolDeleteView.as_view(), name='school_delete'),
    path('schools/detail/<int:pk>/', SchoolDetailView.as_view(), name='school_detail'),
    path('schools/detail/<int:pk>/create-class/', ClassCreateView.as_view(), name='classe_create'),
    #path('classes/create/<int:pk>/', ClasseCreateView.as_view(), name='classe_create'),
    path('classes/detail/<int:pk>/', ClasseDetailView.as_view(), name='classe_detail'),
    path('classes/update/<int:pk>/', ClasseUpdateView.as_view(), name='classe_update'),
    path('classes/delete/<int:pk>/', ClasseDeleteView.as_view(), name='classe_delete'),
    path('load_classes/', views.load_classes, name='load_classes'),
     path('classe/<int:pk>/information/', ClasseInformation.as_view(), name='classe-information'),
    
    # path('cash/accounting_export/', views.cash_accounting_export, name='cash_accounting_export'),
    path('student/<int:pk>/', views.student_detail, name='student_detail'),
    
    path('receipt/print/<int:mouvement_id>/', print_receipt, name='print_receipt'),

   
]