from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

import ollama

from .utils import extract_text_from_pdf


# =========================================================
# OLLAMA SETUP - LOCAL ONLY
# =========================================================

client = ollama.Client(
    host="http://127.0.0.1:11434",
    timeout=300
)


# =========================================================
# 1. HOME VIEW
# =========================================================

def home(request):

    summary = ""
    form = None

    if request.method == "POST":

        print("====================================")
        print("PDF GENERATION REQUEST RECEIVED")
        print("====================================")

        # Check login
        if not request.user.is_authenticated:
            messages.error(
                request,
                "Please login before generating AI notes."
            )
            return redirect("login")

        # Get uploaded PDF
        pdf_file = request.FILES.get("file")

        if not pdf_file:
            messages.error(
                request,
                "Please choose a PDF file."
            )
            return render(
                request,
                "home.html",
                {
                    "summary": summary,
                    "form": form
                }
            )

        print("PDF FILE:", pdf_file.name)

        # Check PDF extension
        if not pdf_file.name.lower().endswith(".pdf"):
            messages.error(
                request,
                "Only PDF files are supported."
            )
            return render(
                request,
                "home.html",
                {
                    "summary": summary,
                    "form": form
                }
            )

        try:

            # =================================================
            # EXTRACT TEXT FROM PDF
            # =================================================

            print("Reading PDF...")

            text = extract_text_from_pdf(pdf_file)

            print("Extracted text length:", len(text))

            if not text.strip():

                messages.error(
                    request,
                    "Could not extract text from this PDF."
                )

                return render(
                    request,
                    "home.html",
                    {
                        "summary": "",
                        "form": form
                    }
                )

            # =================================================
            # AI PROMPT
            # =================================================

            prompt = f"""
You are an AI Study Notes Generator.

Read the following PDF content and create clear,
well-structured and easy-to-understand study notes.

Follow this format:

1. Title
2. Introduction
3. Important Points
4. Detailed Explanation
5. Advantages
6. Disadvantages
7. Applications / Examples
8. Conclusion

Use simple language suitable for college students.

Use headings and bullet points wherever appropriate.

PDF CONTENT:

{text}
"""

            # =================================================
            # CONNECT TO LOCAL OLLAMA
            # =================================================

            print("Connecting to local Ollama...")
            print("Ollama URL: http://127.0.0.1:11434")
            print("Model: llama3.2:3b")

            response = client.chat(
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # =================================================
            # GET AI RESPONSE
            # =================================================

            summary = response["message"]["content"]

            print("====================================")
            print("       AI GENERATION SUCCESS")
            print("====================================")

            return render(
                request,
                "home.html",
                {
                    "summary": summary,
                    "form": form
                }
            )

        except Exception as e:

            print("====================================")
            print("       AI GENERATION ERROR")
            print("====================================")

            print(str(e))

            print("====================================")

            messages.error(
                request,
                f"AI Error: {str(e)}"
            )

            return render(
                request,
                "home.html",
                {
                    "summary": "",
                    "form": form
                }
            )

    return render(
        request,
        "home.html",
        {
            "summary": summary,
            "form": form
        }
    )


# =========================================================
# 2. LOGIN VIEW
# =========================================================

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                "Login successful!"
            )

            return redirect("home")

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

    return render(
        request,
        "login.html"
    )


# =========================================================
# 3. REGISTER VIEW
# =========================================================

def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:

            messages.error(
                request,
                "Username and password are required."
            )

        elif User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

        else:

            User.objects.create_user(
                username=username,
                password=password
            )

            messages.success(
                request,
                "Account created successfully! Please login."
            )

            return redirect("login")

    return render(
        request,
        "register.html"
    )


# =========================================================
# 4. LOGOUT VIEW
# =========================================================

def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out."
    )

    return redirect("login")


# =========================================================
# 5. AI RESPONSE API
# =========================================================

def generate_response(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid request method."
            },
            status=400
        )

    user_prompt = request.POST.get(
        "prompt",
        ""
    ).strip()

    if not user_prompt:

        return JsonResponse(
            {
                "status": "error",
                "message": "Prompt is empty."
            },
            status=400
        )

    try:

        response = client.chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        result_text = response[
            "message"
        ][
            "content"
        ]

        return JsonResponse(
            {
                "status": "success",
                "response": result_text
            }
        )

    except Exception as e:

        return JsonResponse(
            {
                "status": "error",
                "message": str(e)
            },
            status=500
        )