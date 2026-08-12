from django.shortcuts import render
from django.http import JsonResponse
import ollama

# 1. Ngrok URL સેટ કરો (આ લિંક Ngrok CMD વિન્ડોમાંથી મળેલ છે)
NGROK_URL = 'https://reclaim-grid-happy.ngrok-free.dev'

# 2. Ollama Client તૈયાર કરો
client = ollama.Client(host='https://reclaim-grid-happy.ngrok-free.dev')


def generate_response(request):
    """
    આ View ફંકશન Render પરથી રન થશે પણ
    Ngrok ના માધ્યમથી તમારા PC ના Ollama નો ઉપયોગ કરશે.
    """
    if request.method == 'POST':
        user_prompt = request.POST.get('prompt', '')

        try:
            # તમારા PC પર જે મોડેલ ઇન્સ્ટોલ હોય (દા.ત. llama3, mistral, gemma વગેરે) તે વાપરો
            response = client.chat(
                model='llama3',
                messages=[
                    {
                        'role': 'user',
                        'content': user_prompt,
                    },
                ]
            )

            # Ollama માંથી મળેલો જવાબ extract કરો
            result_text = response['message']['content']

            return JsonResponse({'status': 'success', 'response': result_text})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)