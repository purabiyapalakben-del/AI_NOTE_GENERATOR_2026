from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .forms import UploadFileForm
from .utils import extract_text_from_pdf

import ollama


# Home page
def home(request):

    form = UploadFileForm()
    summary = ""

    # User login na hoy to upload allow nahi
    if request.method == "POST":

        if not request.user.is_authenticated:
            return redirect("login")

        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():

            pdf_file = request.FILES["file"]

            text = extract_text_from_pdf(pdf_file)

            prompt = f"""
You are an expert AI Study Notes Generator.

Read the following PDF text carefully and create well-structured study notes.

Instructions:
1. Give a suitable title.
2. Write a short introduction (2-3 lines).
3. Generate 10-15 important bullet points.
4. Explain important concepts briefly.
5. Mention Advantages (if applicable).
6. Mention Disadvantages (if applicable).
7. Mention Applications (if applicable).
8. End with a short conclusion.
9. Use simple English.
10. Do NOT skip important information.

Text:

{text}
"""

            response = ollama.chat(
                model="llama3",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            summary = response["message"]["content"]

    return render(
        request,
        "home.html",
        {
            "form": form,
            "summary": summary
        }
    )


# Register page
def register_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():

            return render(
                request,
                "register.html",
                {
                    "error": "Username already exists"
                }
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect("home")

    return render(request, "register.html")


# Login page
def login_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("home")

        else:

            return render(
                request,
                "login.html",
                {
                    "error": "Invalid username or password"
                }
            )

    return render(request, "login.html")


# Logout page
def logout_view(request):

    logout(request)

    return redirect("login")