from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

import os
import time
from dotenv import load_dotenv
from google import genai

from .utils import extract_text_from_pdf


# =========================================================
# GEMINI SETUP
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set.")

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={
        "api_version": "v1"
    }
)

# Stable Gemini Flash model
GEMINI_MODEL = "gemini-3.6-flash"


# =========================================================
# HELPER FUNCTION - GEMINI RESPONSE
# =========================================================

def generate_gemini_response(prompt, retries=3):
    """
    Generate Gemini response with automatic retry
    for temporary errors such as 503.
    """

    last_error = None

    for attempt in range(retries):

        try:

            print("------------------------------------")
            print("Connecting to Gemini...")
            print("Model:", GEMINI_MODEL)
            print("Attempt:", attempt + 1)
            print("------------------------------------")

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            if response and response.text:
                return response.text

            raise Exception("Gemini returned an empty response.")

        except Exception as e:

            last_error = e

            error_text = str(e).lower()

            print("Gemini Error:", str(e))

            # Retry temporary server errors
            if (
                "503" in error_text
                or "unavailable" in error_text
                or "high demand" in error_text
                or "429" in error_text
                or "rate" in error_text
            ):

                if attempt < retries - 1:

                    wait_time = 2 ** attempt

                    print(
                        f"Temporary Gemini error. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

            # Other errors should stop immediately
            raise e

    raise last_error


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

        # -------------------------------------------------
        # LOGIN CHECK
        # -------------------------------------------------

        if not request.user.is_authenticated:

            messages.error(
                request,
                "Please login before generating AI notes."
            )

            return redirect("login")

        # -------------------------------------------------
        # GET FILE
        # -------------------------------------------------

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
                    "summary": "",
                    "form": form
                }
            )

        print("Uploaded file:", pdf_file.name)

        # -------------------------------------------------
        # CHECK PDF EXTENSION
        # -------------------------------------------------

        if not pdf_file.name.lower().endswith(".pdf"):

            messages.error(
                request,
                "Only PDF files are supported."
            )

            return render(
                request,
                "home.html",
                {
                    "summary": "",
                    "form": form
                }
            )

        try:

            # =================================================
            # EXTRACT TEXT FROM PDF
            # =================================================

            print("Reading PDF...")

            text = extract_text_from_pdf(pdf_file)

            print(
                "Extracted text length:",
                len(text)
            )

            if not text or not text.strip():

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

Read the following PDF content and create
clear, well-structured and easy-to-understand
study notes.

Follow this format:

1. Title
2. Introduction
3. Important Points
4. Detailed Explanation
5. Advantages
6. Disadvantages
7. Applications / Examples
8. Conclusion

Instructions:

- Use simple language suitable for college students.
- Use clear headings.
- Use bullet points wherever appropriate.
- Keep the explanation accurate and easy to study.
- Make the notes useful for exam preparation.
- Do not add unrelated information.
- Base the answer only on the provided PDF content.
- Do not mention that you are an AI.
- Make the notes clean and well formatted.

PDF CONTENT:

{text}
"""

            # =================================================
            # GENERATE AI NOTES
            # =================================================

            summary = generate_gemini_response(prompt)

            print("====================================")
            print("AI GENERATION SUCCESS")
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
            print("AI GENERATION ERROR")
            print("====================================")

            print(str(e))

            print("====================================")

            error_text = str(e).lower()

            # -------------------------------------------------
            # USER FRIENDLY ERROR MESSAGES
            # -------------------------------------------------

            if (
                "503" in error_text
                or "unavailable" in error_text
                or "high demand" in error_text
            ):

                error_message = (
                    "Gemini is temporarily busy. "
                    "Please try again after a few seconds."
                )

            elif (
                "429" in error_text
                or "quota" in error_text
                or "rate" in error_text
            ):

                error_message = (
                    "Gemini API limit has been reached. "
                    "Please try again later."
                )

            elif (
                "api key" in error_text
                or "authentication" in error_text
                or "permission" in error_text
            ):

                error_message = (
                    "Gemini API authentication failed. "
                    "Please check your API key."
                )

            else:

                error_message = (
                    f"AI Error: {str(e)}"
                )

            messages.error(
                request,
                error_message
            )

            return render(
                request,
                "home.html",
                {
                    "summary": "",
                    "form": form
                }
            )

    # =========================================================
    # GET REQUEST
    # =========================================================

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

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

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

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not username or not password:

            messages.error(
                request,
                "Username and password are required."
            )

        # -------------------------------------------------
        # CHECK USERNAME
        # -------------------------------------------------

        elif User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

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

    # -------------------------------------------------
    # REQUEST METHOD
    # -------------------------------------------------

    if request.method != "POST":

        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid request method."
            },
            status=400
        )

    # -------------------------------------------------
    # LOGIN CHECK
    # -------------------------------------------------

    if not request.user.is_authenticated:

        return JsonResponse(
            {
                "status": "error",
                "message": "Please login first."
            },
            status=401
        )

    # -------------------------------------------------
    # GET PROMPT
    # -------------------------------------------------

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

        # -------------------------------------------------
        # GEMINI
        # -------------------------------------------------

        result_text = generate_gemini_response(
            user_prompt
        )

        return JsonResponse(
            {
                "status": "success",
                "response": result_text
            }
        )

    except Exception as e:

        print(
            "AI RESPONSE ERROR:",
            str(e)
        )

        error_text = str(e).lower()

        if (
            "503" in error_text
            or "unavailable" in error_text
            or "high demand" in error_text
        ):

            message = (
                "Gemini is temporarily busy. "
                "Please try again."
            )

        elif (
            "429" in error_text
            or "quota" in error_text
            or "rate" in error_text
        ):

            message = (
                "Gemini API limit has been reached."
            )

        else:

            message = str(e)

        return JsonResponse(
            {
                "status": "error",
                "message": message
            },
            status=500
        )