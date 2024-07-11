from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout,get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, Candidate, Position, Vote
from .forms import UserCreationForm, CandidateForm, PositionForm
from django.db.models import Count
from django.contrib import messages
import csv
from django.http import HttpResponse
from django.db import transaction





User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.is_admin



def home(request):
    return render(request, 'voting/home.html')


@user_passes_test(is_admin)
def admin_dashboard(request):
    positions = Position.objects.all()
    voting_data = {}

    for position in positions:
        votes = Vote.objects.filter(candidate__position=position)\
                            .values('candidate__name')\
                            .annotate(count=Count('id'))\
                            .order_by('-count')
        
        # Include candidates with zero votes
        all_candidates = Candidate.objects.filter(position=position)
        candidate_votes = {vote['candidate__name']: vote['count'] for vote in votes}
        
        position_data = [
            {
                'candidate__name': candidate.name,
                'count': candidate_votes.get(candidate.name, 0)
            }
            for candidate in all_candidates
        ]
        
        voting_data[position.title] = position_data

    context = {
        'voting_data': voting_data,
    }
    return render(request, 'voting/admin_dashboard.html', context)
# def admin_dashboard(request):
#     positions = Position.objects.all()
#     voting_data = {}

#     for position in positions:
#         votes = Vote.objects.filter(candidate__position=position)\
#                             .values('candidate__name')\
#                             .annotate(count=Count('id'))\
#                             .order_by('-count')
#         voting_data[position.title] = list(votes)

#     context = {
#         'voting_data': voting_data,
#     }
#     return render(request, 'voting/admin_dashboard.html', context)


@user_passes_test(lambda u: u.is_admin)
def add_voter(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            User.objects.create_user(email=email, password=password, username=email)
            messages.success(request, 'Voter added successfully.')
            return redirect('admin_dashboard')
        except:
            messages.error(request, 'Error adding voter. Email may already be in use.')
    return render(request, 'voting/add_voter.html')


@user_passes_test(lambda u: u.is_admin)
def add_candidate(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidate added successfully.')
            return redirect('admin_dashboard')
    else:
        form = CandidateForm()
    return render(request, 'voting/add_candidate.html', {'form': form})



# @login_required
# def vote(request):
#     # Check if the user has already voted
#     if Vote.objects.filter(voter=request.user).exists():
#         messages.error(request, "You have already cast your vote.")
#         return redirect('thank_you')

#     if request.method == 'POST':
#         positions = Position.objects.all()
#         votes_to_create = []
#         for position in positions:
#             candidate_id = request.POST.get(f'candidate_{position.id}')
#             if candidate_id:
#                 try:
#                     candidate = Candidate.objects.get(id=candidate_id, position=position)
#                     votes_to_create.append(Vote(voter=request.user, candidate=candidate))
#                 except Candidate.DoesNotExist:
#                     messages.error(request, f"Invalid candidate selection for position: {position.title}")
#                     return render(request, 'voting/voting_page.html', {'positions': positions})
#             else:
#                 messages.warning(request, f"You didn't select a candidate for the position: {position.title}")
#                 return render(request, 'voting/voting_page.html', {'positions': positions})
        
#         # If we've made it this far, create all votes in a single transaction
#         try:
#             with transaction.atomic():
#                 Vote.objects.bulk_create(votes_to_create)
#             messages.success(request, "Your votes have been successfully recorded.")
#             return redirect('thank_you')
#         except IntegrityError:
#             messages.error(request, "An error occurred while recording your votes. Please try again.")
#             return render(request, 'voting/voting_page.html', {'positions': positions})
    
#     positions = Position.objects.all()
#     return render(request, 'voting/voting_page.html', {'positions': positions})

@login_required
def vote(request):
    # Check if the user has already voted
    if Vote.objects.filter(voter=request.user).exists():
        messages.error(request, "You have already cast your vote.")
        return redirect('thank_you')

    if request.method == 'POST':
        positions = Position.objects.all()
        votes_to_create = []
        all_positions_voted = True

        for position in positions:
            candidate_id = request.POST.get(f'candidate_{position.id}')
            
            # Debugging: Print the received candidate_id for each position
            print(f"Position: {position.title}, Candidate ID: {candidate_id}")

            if candidate_id:
                try:
                    candidate = Candidate.objects.get(id=candidate_id, position=position)
                    votes_to_create.append(Vote(voter=request.user, candidate=candidate))
                except Candidate.DoesNotExist:
                    messages.error(request, f"Invalid candidate selection for position: {position.title}")
                    all_positions_voted = False
                    break
            else:
                messages.warning(request, f"You didn't select a candidate for the position: {position.title}")
                all_positions_voted = False
                break
        
        if all_positions_voted:
            try:
                with transaction.atomic():
                    Vote.objects.bulk_create(votes_to_create)
                messages.success(request, "Your votes have been successfully recorded.")
                return redirect('thank_you')
            except IntegrityError:
                messages.error(request, "An error occurred while recording your votes. Please try again.")
        
        # If we get here, it means not all positions were voted for or there was an error
        return render(request, 'voting/voting_page.html', {'positions': positions})
    
    positions = Position.objects.all()
    return render(request, 'voting/voting_page.html', {'positions': positions})


@login_required
def thank_you(request):
    return render(request, 'voting/thank_you.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if user.is_admin:
                return redirect('admin_dashboard')
            else:
                return redirect('vote')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'voting/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@user_passes_test(lambda u: u.is_admin)
def reset_votes(request):
    if request.method == 'POST':
        Vote.objects.all().delete()
        messages.success(request, 'All votes have been reset successfully.')
    else:
        messages.error(request, 'Invalid request method for vote reset.')
    return redirect('admin_dashboard')


@user_passes_test(lambda u: u.is_admin)
def print_results(request):
    positions = Position.objects.all()
    results = {}

    for position in positions:
        votes = Vote.objects.filter(candidate__position=position)\
                            .values('candidate__name')\
                            .annotate(count=Count('id'))\
                            .order_by('-count')
        
        # Include candidates with zero votes
        all_candidates = Candidate.objects.filter(position=position)
        candidate_votes = {vote['candidate__name']: vote['count'] for vote in votes}
        
        position_results = [
            {
                'name': candidate.name,
                'votes': candidate_votes.get(candidate.name, 0)
            }
            for candidate in all_candidates
        ]
        
        results[position.title] = position_results

    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="voting_results.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Position', 'Candidate', 'Votes'])
        
        for position, candidates in results.items():
            for candidate in candidates:
                writer.writerow([position, candidate['name'], candidate['votes']])
        
        return response

    return render(request, 'voting/print_results.html', {'results': results})


def candidates_list(request):
    candidates = Candidate.objects.all().select_related('position')
    voters = User.objects.all()
    positions = Position.objects.all()
    votes = Vote.objects.all().select_related('voter', 'candidate')

    context = {
        'candidates': candidates,
        'voters': voters,
        'positions': positions,
        'votes': votes,
    }

    return render(request, 'voting/candidate_list.html', context)
