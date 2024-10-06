import os
import git
import markdown
from bs4 import BeautifulSoup
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 없습니다")

os.environ["OPENAI_API_KEY"] = openai_api_key


def clone_repo(repo_url, local_path):
    """GitHub 저장소를 클론합니다."""
    if not os.path.exists(local_path):
        git.Repo.clone_from(repo_url, local_path)
    else:
        print(f"저장소가 이미 {local_path}에 존재합니다")


def extract_text_from_md(file_path):
    """Markdown 파일에서 텍스트 콘텐츠를 추출합니다."""
    with open(file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()

    # Markdown을 HTML로 변환
    html_content = markdown.markdown(md_content)

    # HTML을 파싱하고 텍스트 추출
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()


def process_md_files(repo_path):
    """저장소 내의 모든 Markdown 파일을 처리합니다."""
    all_text = ""
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                all_text += extract_text_from_md(file_path) + "\n\n"
    return all_text


def create_knowledge_base(text):
    """추출된 텍스트로부터 지식 기반을 생성합니다."""
    # 텍스트를 여러 청크로 분할
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(text)

    # 임베딩 생성
    embeddings = OpenAIEmbeddings()

    # 벡터스토어 생성 및 영구 저장
    vectorstore = Chroma.from_texts(texts, embeddings, persist_directory="./knowledge_base")
    vectorstore.persist()

    return vectorstore


def main():
    # GitHub 저장소 URL 및 로컬 경로 설정
    repo_url = "https://github.com/JaeYeopHan/Interview_Question_for_Beginner.git"
    local_path = "./Interview_Question_for_Beginner"

    # 저장소 클론
    clone_repo(repo_url, local_path)

    # Markdown 파일 처리
    all_text = process_md_files(local_path)

    # 지식 기반 생성
    vectorstore = create_knowledge_base(all_text)

    print("지식 기반 생성 완료!")


if __name__ == "__main__":
    main()
