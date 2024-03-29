import json
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout as lgt
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from project.forms import PostForm, UserCreateForm
from project.models import FriendRequest, Message, Post, User
from project.serializers import UserSerializer


@login_required(login_url='login')
def home_page(request):
    context = {
        'user': request.user,
        'posts': Post.objects.filter(creator=request.user),
        'friends': request.user.friends.all(),
        'user_friends': request.user.friends.all(),
    }

    if request.method == 'POST':
        post_id = request.POST.get('id')
        print(post_id)

        match post_id:
            case 'ADD-POST':
                form = PostForm({**{key: value for key, value in request.POST.items()}, 'creator': request.user}, request.FILES)

                if form.is_valid():
                    form.save()

            case 'UPDATE-IMAGE':
                image = request.FILES.get('image')
                
                if image:
                    user = request.user

                    user.avatar = image
                    user.save()

            case 'UPDATE-BACKGROUND-IMAGE':
                image = request.FILES.get('image')
                
                if image:
                    user = request.user

                    user.background_image = image
                    user.save()

        return redirect(request.META.get('HTTP_REFERER', 'home'))

    return render(request, "profile.html", context)


def login_page(request):
    context = {}

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')


        if username and password:

            user = User.objects.filter(username=username)

            if user.exists() and user.first().check_password(password):

                login(request, user.first())

                return redirect('home')
            
            else:
                context['error'] = 'Password didn\'t match or user not found'


    return render(request, 'auth/login.html', context)


def register_page(request):
    context = {}

    if request.method == 'POST':
        form = UserCreateForm(request.POST)

        if form.is_valid():
            login(request, form.save())

            return redirect('home')

        context['form_errors'] = form.errors

    return render(request, 'auth/register.html', context)


def logout(request):
    lgt(request)
    return redirect('login')


@login_required(login_url='login')
def user_profile(request, username):

    user = User.objects.get(username=username)

    context = {
        'user': user,
        'posts': Post.objects.filter(creator=user),
        'friends': user.friends.exclude(friend=request.user),
        'user_friends': request.user.friends.all(),
    }
    return render(request, "profile.html", context)


@login_required(login_url='login')
def chat_page(request, username):
    receiver = User.objects.get(username=username)
    queryset = Message.objects.filter(Q(sender=request.user, receiver=receiver) | Q(receiver=request.user, sender=receiver)).order_by('created_at')
    
    messages = []

    for msg in queryset:
        
        minute = msg.created_at.minute
        hour = msg.created_at.hour

        if len(messages) == 0 or messages[-1]['sender']['id'] != msg.sender.pk or messages[-1]['sender']['id'] == msg.sender.pk and minute - int(messages[-1]['messages'][-1]['created_at'].split(':')[-1]) > 3 or hour != int(messages[-1]['messages'][-1]['created_at'].split(':')[0]):
            messages.append(
                {
                    'sender': UserSerializer(msg.sender).data,
                    'receiver': UserSerializer(msg.receiver).data,
                    'messages': [
                        {
                            'pk': msg.pk,
                            'text': msg.text,
                            'created_at': msg.created_at.strftime('%H:%M')
                        },
                    ]
                }
            )     
        else:
            messages[-1]['messages'].append(
                {
                    'pk': msg.pk,
                    'text': msg.text,
                    'created_at': msg.created_at.strftime('%H:%M')
                }
            )

    context = {
        'receiver': receiver,
        'messages': messages,
        'user_friends': request.user.friends.all(),
    }

    return render(request, 'chat.html', context)


def send_friend_request(request, pk):
    user = User.objects.filter(pk=pk)
    

    if user.exists() and not FriendRequest.objects.filter(_from=request.user, to=user.first()).exists():
        FriendRequest.objects.create(_from=request.user, to=user.first())

    return redirect(request.META.get('HTTP_REFERER', 'home'))
