import os
import time
import pandas as pd
import pdfplumber
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from secrets_manager import get_api_keys
from slugify import slugify
import chardet

# OpenAI API 키 설정
openai_api_key, pinecone_api_key = get_api_keys()

# Pinecone API 설정
environment = "us-east1-gcp"
index_name = "project3"

os.environ["OPENAI_API_KEY"] = openai_api_key

# Pinecone 클라이언트 초기화
pc = Pinecone(api_key=pinecone_api_key)
embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

# Pinecone 인덱스 생성
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="awp",
            region="us-east1"
        )
    )

pinecine_index = pc.Index(index_name)

def generate_with_gpt(prompt, model="gpt-3.5-turbo"):
    try:
        prompt = prompt[:3000]
        response = OpenAI(api_key=openai_api_key).chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            n=1,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT 생성 중 오류 발생: {e}")
        return None

def load_file(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()  # 파일 확장자 추출
    content = ""

    if ext == 'pdf':
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                content += page.extract_text()
    elif ext == 'csv':
        # 인코딩 자동 감지
        raw_data = uploaded_file.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding'] if detected['confidence'] > 0.5 else 'utf-8'
        uploaded_file.seek(0)  # 파일 포인터 초기화
        try:
            df = pd.read_csv(uploaded_file, encoding=encoding)
            content = df.to_string()
        except Exception as e:
            print(f"CSV 파일 읽기 오류: {e}")
    elif ext == 'txt':
        content = uploaded_file.read().decode('utf-8')
    elif ext == 'xlsx':
        df = pd.read_excel(uploaded_file)
        content = df.to_string()
    else:
        print(f"지원하지 않는 파일 형식입니다: {ext}")

    return content

def get_existing_ids(index):
    existing_ids = []
    try:
        # Pinecone에서 데이터 100개를 가져오기
        fetch_response = index.fetch(ids=[f"chunk_{i}" for i in range(100)])
        existing_ids = [item.id for item in fetch_response['vectors'].values()]
    except Exception as e:
        print(f"데이터 확인 중 오류 발생: {e}")
    return existing_ids

def upload_data_if_not_exists(split_texts, index, file_name):
    # 기존 데이터 ID 가져오기
    existing_ids = get_existing_ids(index)

    for i, doc in enumerate(split_texts):
        # 파일명과 번호를 결합한 ID 생성
        chunk_id = f"{file_name}_{i}"

        if chunk_id not in existing_ids:
            try:
                time.sleep(0.1)  # Rate Limiting 방지
                vector = embedding_model.embed_query(doc.page_content)  # 텍스트 임베딩 생성
                index.upsert([(chunk_id, vector, {"source": chunk_id, "text": doc.page_content})])  # Pinecone에 업로드
                print(f"업로드된 ID: {chunk_id}")
            except Exception as e:
                print(f"chunk_{i}에서 오류 발생: {e}")
        else:
            print(f"ID {chunk_id}는 이미 Pinecone에 존재합니다. 업로드를 건너뜁니다.")

def split_text(content):
    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=50)

    # 문자열을 Document 객체로 변환하여 반환
    documents = text_splitter.split_text(content)
    return [Document(page_content=doc) for doc in documents]  # Document 객체로 반환

def search_in_pinecone(query, index, embedding_model, top_k=3):
    try:
        # 쿼리 임베딩 생성
        query_vector = embedding_model.embed_query(query)

        # Pinecone 인덱스에서 검색
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        return results
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        return None

def process_search_results(search_results, prompt):
    if search_results and search_results['matches']:
        # 검색 결과 중 점수가 가장 높은 항목 가져오기
        best_match = max(search_results['matches'], key=lambda match: match['score'])

        if best_match['score'] < 0.85:
            # print(best_match['score'])
            return "관련 내용이 없습니다. 관련 파일을 업로드 후 다시 질문해주세요."
        else:
            # 검색된 텍스트를 결합하여 GPT에게 전달할 프롬프트
            context = "\n".join([match['metadata']['text'] for match in search_results['matches'] if match['score'] >= 0.8])
            gpt_prompt = f"다음 내용을 바탕으로 사용자의 질문에 답해주세요: {prompt}\n\n{context}"
            return generate_with_gpt(gpt_prompt)
    else:
        return "검색 결과가 없습니다."
