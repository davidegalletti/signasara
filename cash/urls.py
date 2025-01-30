from django.urls import path
from . import views
from .views import (
   
      UniformPaymentListView, 
      
        UniformReservationListView,
    UniformReservationCreateView,
    UniformReservationUpdateView,
    UniformReservationDeleteView, student_search
    
)
urlpatterns = [
    path('uniform_payments/', UniformPaymentListView.as_view(), name='uniform_payments'),
     path('reservations/', UniformReservationListView.as_view(), name='uniform-reservation-list'),
    path('api/student-search/', student_search, name='student-search'),
    path('reservations/add/<int:student_pk>/', UniformReservationCreateView.as_view(), name='uniform-reservation-add'),
    path('reservations/add/', UniformReservationCreateView.as_view(), name='uniform-reservation-add'),
    path('reservations/<int:pk>/edit/', UniformReservationUpdateView.as_view(), name='uniform-reservation-edit'),
    path('reservations/<int:pk>/delete/', UniformReservationDeleteView.as_view(), name='uniform-reservation-delete'),
    path('update_paiement/<int:pk>/', views.update_paiement, name='update_paiement'),
    path('add_paiement/<int:pk>/', views.add_payment, name='add_paiement'),
      path('class/<int:pk>/manage-tarifs/', views.manage_tarifs, name='manage_tarifs'),
    path('class/<int:pk>/add-tarif/', views.add_tarif, name='add_tarif'),
    path('tarif/<int:pk>/edit/', views.update_tarif, name='update_tarif'),
    path('tarif/<int:pk>/delete/', views.delete_tarif, name='delete_tarif'),
    path('cash/flow_report/', views.cash_flow_report, name='cash_flow_report'),
    path('mouvements/', views.mouvement_list, name='mouvement_list'),
    path('mouvements/add/', views.add_mouvement, name='add_mouvement'),
    path('mouvements/update/<int:pk>/', views.update_mouvement, name='update_mouvement'),
    path('mouvements/delete/<int:pk>/', views.delete_mouvement, name='delete_mouvement'),
    path('late_payment_report/', views.late_payment_report, name='late_payment_report'),
    path('class/<int:pk>/manage-tarifs/', views.manage_tarifs, name='manage_tarifs'),
    path('accounting_c_sco_report/', views.accounting_c_sco_report, name='accounting_c_sco_report'),
    path('accounting_c_sco_report/<str:period>/', views.accounting_c_sco_report, name='accounting_c_sco_report_period'),
 # Accounting Report - Bi-Monthly
    path('c_sco/accounting/bi_monthly/', views.accounting_c_sco_report, {'period': 'bi_monthly'}, name='accounting_c_sco_report_bi_monthly'),

]