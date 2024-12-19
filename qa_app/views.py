from django.shortcuts import render
from django.http import JsonResponse
from .forms import FileUploadForm
from .utils import load_file, split_text, upload_data_if_not_exists, search_in_pinecone, generate_with_gpt, pinecine_index, embedding_model, process_search_results
from django.views.decorators.csrf import csrf_exempt
from slugify import slugify
import json

def home(request):
    return render(request, 'base.html')

def upload(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # 파일 이름을 ASCII 형식으로 변환
            original_file_name = uploaded_file.name.split('.')[0]
            sanitized_file_name = slugify(original_file_name) # slugify 사용
            
            file_content = load_file(uploaded_file)
            split_texts = split_text(file_content)
            
            # 변환된 파일 이름을 사용하여 Pinecone에 업로드
            upload_data_if_not_exists(split_texts, pinecine_index, sanitized_file_name)
            return JsonResponse({'message': '파일이 성공적으로 처리되었습니다.'})
        else:
            return JsonResponse({'message': '파일 업로드에 실패했습니다.'}, status=400)
    else:
        form = FileUploadForm()
    return render(request, '', {'form': form})

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query')
        model = data.get('model', 'gpt-3.5-turbo')
        
        search_results = search_in_pinecone(query, pinecine_index, embedding_model)
        
        if search_results:
            response_gpt = process_search_results(search_results, query)
            
            if response_gpt == "관련 내용이 없습니다. 관련 파일을 업로드 후 다시 질문해주세요.":
                return JsonResponse({'answer': response_gpt})
            else:
                return JsonResponse({
                    'answer': response_gpt,
                    'sources': [
                        {
                            'text': match['metadata'].get('text', '')[:400],
                            'source': match['metadata'].get('source', '알 수 없음').split('_')[1]
                        } for match in search_results['matches'] if match['score'] >= 0.8
                    ]
                })
        else:
            return JsonResponse({'answer': '검색 결과가 없습니다.'})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

