from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('vote/', views.vote, name='vote'),
    path('thank-you/', views.thank_you, name='thank_you'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-voter/', views.add_voter, name='add_voter'),
    path('add-candidate/', views.add_candidate, name='add_candidate'),
    path('candidate-list/', views.candidates_list, name='candidate_list'),
    path('reset-votes/', views.reset_votes, name='reset_votes'),
    path('print-results/', views.print_results, name='print_results'),
]