from django.http import HttpRequest
from django.shortcuts import redirect,render,get_object_or_404
#importing for auth 
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
#for login required
from django.contrib.auth.decorators import login_required
#importing sendmail
from django.core.mail import send_mail
#importing jasonresponse
from django.http import JsonResponse
#importing conversation
from services.models import Conversation,ConversationParticipant,Message,UserProfile



def userlogin(request):
    #loggin in if user name n password is correct
    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.is_online = True
            profile.save()
            return redirect('homepage')
        else:
            return render(request, "userlogin.html", {
                'loginerror': 'invalid username or password'
            })
        

    return render(request,"userlogin.html")

def userregistration(request):
    #getting data from registration page to auth_user database
    if request.method == "POST":
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        #checking if username already exists
        if User.objects.filter(username=username).exists():
            return render(request,"userregistration.html",{'username_error': 'Username already exists'})

        #checking if email exists or not
        if User.objects.filter(email=email).exists():
            return render(
                request,
                "userregistration.html",
                {"email_error": "Email already exists"}
            )

        #checking passwords and confirm passwords are same or not
        if password!=confirm_password:    
            return render(request,"userregistration.html",{'password_error': 'Password does not match'})

        #saving data into auth_user table
        user=User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
        UserProfile.objects.create(
        user=user
        )

        #sending mail on the mail u have given
        send_mail(
            "Real Time Auction.com",
            f"Thank You {username} u have Successfully Registered on Real Time Chat.com",
            "aadityakalgaonkar@gmail.com",
            [email],
            fail_silently=False
        )
        return redirect('login') 
    return render(request,"userregistration.html")

@login_required
def homepage(request):
    conversations = Conversation.objects.filter(
        conversationparticipant__user=request.user
    ).distinct()

    chat_list = []

    for conversation in conversations:

        other_participant = ConversationParticipant.objects.filter(
            conversation=conversation
        ).exclude(
            user=request.user
        ).first()

        if other_participant:

            chat_list.append({
                "conversation_id": conversation.id,
                "username": other_participant.user.username,
                "user_id": other_participant.user.id
            })

    return render(request,"homepage.html",{"chat_list": chat_list})

def userlogout(request):

    profile = UserProfile.objects.get(user=request.user)
    profile.is_online = False
    profile.save()
    logout(request)

    return redirect('login')

@login_required
def search_user(request):

    #for searching the names on search bar from user tables 
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse([], safe=False)

    users = User.objects.filter(
        username__icontains=query
    ).exclude(id=request.user.id)

    data = []

    for user in users:
        data.append({
            "id": user.id,
            "username": user.username
        })

    return JsonResponse(data, safe=False)

@login_required
def chat(request, conversation_id):

    # Get conversation
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
    )

    # Security check
    if not ConversationParticipant.objects.filter(
        conversation=conversation,
        user=request.user
    ).exists():

        return redirect("homepage")

    # Get other participant
    other_participant = ConversationParticipant.objects.filter(
        conversation=conversation
    ).exclude(
        user=request.user
    ).first()

    # Load all messages
    messages = Message.objects.filter(
        conversation=conversation
    ).select_related(
        "sender"
    ).order_by(
        "timestamp"
    )
    profile,created = UserProfile.objects.get_or_create(
    user=other_participant.user
    )
    return render(
        request,
        "chat.html",
        {
            "conversation": conversation,
            "other_user": other_participant.user,
            "messages": messages,
            "profile":profile
        }
    )

@login_required
def open_chat(request, user_id):

    other_user = User.objects.get(id=user_id)

    # Get all conversations of logged-in user
    my_conversations = Conversation.objects.filter(
        conversationparticipant__user=request.user
    )

    conversation = None

    # Check whether other user is also in the same conversation
    for conv in my_conversations:

        if ConversationParticipant.objects.filter(
            conversation=conv,
            user=other_user
        ).exists():

            conversation = conv
            break

    # If conversation doesn't exist, create one
    if conversation is None:

        conversation = Conversation.objects.create()

        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user
        )

        ConversationParticipant.objects.create(
            conversation=conversation,
            user=other_user
        )

    return redirect("chat", conversation_id=conversation.id)