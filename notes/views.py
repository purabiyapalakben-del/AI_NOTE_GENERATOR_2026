from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import ollama


# Ngrok Setup
NGROK_URL = "https://reclaim-grid-happy.ngrok-free.dev"
client = ollama.Client(host=NGROK_URL)


# 1. Home View
def home(request):
    return render(request, "home.html")


# 2. Login View
def login_view(request):
    if request.method == "POST":
        u_name = request.POST.get("username")
        p_word = request.POST.get("password")

        user = authenticate(
            request,
            username=u_name,
            password=p_word
        )

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(
                request,
                "Invalid username or password"
            )

    return render(request, "login.html")


# 3. Register View
def register_view(request):
    if request.method == "POST":
        u_name = request.POST.get("username")
        p_word = request.POST.get("password")

        if User.objects.filter(username=u_name).exists():
            messages.error(
                request,
                "Username already exists"
            )
        else:
            User.objects.create_user(
                username=u_name,
                password=p_word
            )

            messages.success(
                request,
                "Account created successfully! Please login."
            )

            return redirect("login_view")

    return render(request, "register.html")


# 4. Logout View
def logout_view(request):
    logout(request)
    return redirect("login_view")


# 5. AI Note Generator Response View
def generate_response(request):
    if request.method == "POST":
        user_prompt = request.POST.get("prompt", "")

        try:
            response = client.chat(
                model="llama3",
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            result_text = response["message"]["content"]

            return JsonResponse({
                "status": "success",
                "response": result_text
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=400)