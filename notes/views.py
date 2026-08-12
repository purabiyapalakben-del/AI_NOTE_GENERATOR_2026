from django.shortcuts import render
from django.http import JsonResponse
import ollama

# Ngrok Client Setup
NGROK_URL = 'https://reclaim-grid-happy.ngrok-free.dev'
client = ollama.Client(host=NGROK_URL)



def home(request):
    return render(request, 'home.html')
def register_view(request):
    return render(request, 'register.html')
def login_views(request):
    return render(request, 'login.html')


# 2. Response Viewa
def generate_response(request):
    if request.method == 'POST':
        user_prompt = request.POST.get('prompt', '')

        try:
            response = client.chat(
                model='llama3',
                messages=[
                    {
                        'role': 'user',
                        'content': user_prompt,
                    },
                ]
            )
            result_text = response['message']['content']
            return JsonResponse({'status': 'success', 'response': result_text})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)