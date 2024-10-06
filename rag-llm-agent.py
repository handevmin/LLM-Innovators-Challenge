import os
from dotenv import load_dotenv
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.tools import BaseTool
import speech_recognition as sr
import pyttsx3
from typing import Any

# 환경 변수 로드
load_dotenv()

# Upstage API 키 설정
upstage_api_key = os.getenv("UPSTAGE_API_KEY")
if not upstage_api_key:
    raise ValueError(".env 파일에서 UPSTAGE_API_KEY를 찾을 수 없습니다.")
os.environ["UPSTAGE_API_KEY"] = upstage_api_key

# 임베딩 및 벡터 저장소 초기화
embeddings_model = UpstageEmbeddings(model="solar-embedding-1-large-query")
vectorstore = Chroma(persist_directory="./knowledge_base", embedding_function=embeddings_model)

# LLM 초기화
llm = ChatUpstage(
    temperature=0.5,
    model_name="solar-1-mini-chat",
)

# 검색 기반 QA 체인 생성
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())


# 사용자 정의 도구 정의
class InterviewQuestionGenerator(BaseTool):
    name: str = "면접 질문 생성기"
    description: str = "사용자 프로필, 회사 정보, 직무 관심사를 기반으로 개인화된 면접 질문을 생성합니다."

    def _run(self, query: str) -> str:
        prompt = f"다음 정보를 바탕으로 면접 질문을 생성해주세요: {query}. 질문은 한국어로 생성해주세요."
        return llm(prompt)

    def _arun(self, query: str) -> Any:
        raise NotImplementedError("이 도구는 비동기 실행을 지원하지 않습니다.")


question_generator = InterviewQuestionGenerator()

tools = [
    Tool(name="회사 정보", func=qa.invoke, description="회사에 대한 정보를 검색합니다"),
    Tool(name="질문 생성기", func=question_generator._run, description="면접 질문을 생성합니다")
]

# 에이전트 초기화
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True,
                         early_stopping_method="force")

# 음성 인식 및 합성 설정
recognizer = sr.Recognizer()
engine = pyttsx3.init()


# TTS 설정
def setup_tts():
    voices = engine.getProperty('voices')
    for voice in voices:
        if "korean" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 150)


setup_tts()


# 사용자 입력을 받는 함수 (텍스트 또는 음성)
def get_user_input(prompt, speech=False):
    if speech:
        with sr.Microphone() as source:
            print(prompt)
            engine.say(prompt)
            engine.runAndWait()
            print("말씀해 주세요...")
            audio = recognizer.listen(source)
            try:
                user_input = recognizer.recognize_google(audio, language="ko-KR")
                print(f"인식된 음성: {user_input}")
                return user_input
            except sr.UnknownValueError:
                print("죄송합니다. 음성을 인식하지 못했습니다. 다시 시도해 주세요.")
                return get_user_input(prompt, speech)
            except sr.RequestError:
                print("음성 인식 서비스에 접근할 수 없습니다. 텍스트로 입력해 주세요.")
                return input(prompt)
    else:
        return input(prompt)


# AI 응답을 제공하는 함수 (텍스트 및 음성)
def provide_ai_response(response, speech=True):
    print(response)
    if speech:
        engine.say(response)
        engine.runAndWait()


# 주요 면접 시뮬레이션 함수
def interview_simulation():
    # 사용자 프로필 받기
    # user_profile = get_user_input("귀하의 프로필을 입력해주세요 (경력, 학력, 기술 스택 등): ", speech=True)
    user_profile = "경력: 경력없음, 학력: 대졸, 기술 스택: 백엔드"
    # 목표 회사 받기
    # company_name = get_user_input("어느 회사에 지원하시나요? ", speech=True)
    company_name = "삼성전자"
    # 관심 직무 받기 (텍스트 입력)
    # job_interest = input("어떤 직무에 관심이 있으신가요? ")
    job_interest = "백엔드"
    # 면접 유형 선택
    # interview_type = input("면접 유형을 선택해주세요 (기술면접, 인성면접, 자기소개서 기반 면접): ")
    interview_type = "기술면접"
    resume = ""
    if interview_type == "자기소개서 기반 면접":
        resume = input("자기소개서를 입력해주세요: ")

    # 면접 분위기 선택
    # interview_atmosphere = input("면접 분위기를 선택해주세요 (일반 면접, 압박 면접): ")
    interview_atmosphere = "일반 면접"
    # 면접관 persona 설정
    if interview_atmosphere == "일반 면접":
        persona = "당신은 친절하고 편안한 성격의 면접관입니다. 지원자가 편안하게 답변할 수 있도록 친절한 말투로 질문하세요."
    elif interview_atmosphere == "압박 면접":
        persona = "당신은 예리하고 꼼꼼하며 비판적인 성격의 면접관입니다. 지원자의 답변에 모순이나 추가 설명이 필요한 부분을 집중적으로 파고들어 질문하세요."
    else:
        raise ValueError("면접 분위기는 '일반 면접' 또는 '압박 면접' 중에서 선택해야 합니다.")

    # 회사 정보 검색
    company_info = agent.invoke(
        f"{company_name}에 대한 정보를 검색해주세요. 만약 정보가 없다면, 일반적인 IT 회사의 정보를 제공해주세요.")

    review = []
    context = ""

    # num_questions = int(input("면접 질문 수를 입력해주세요: "))
    num_questions = 5
    for i in range(num_questions):
        if interview_type == "기술면접":
            question_prompt = f"{persona} 다음 정보를 바탕으로 IT 기업의 기술면접에서 물어볼 수 있는 구체적이고 관련성 있는 질문을 생성해주세요. 질문은 한 문장으로, 직접적이고 명확하게 만들어주세요. 특히 관심 직무에 적합한 질문을 생성해주세요: 지원자 프로필: {user_profile}, 회사 정보: {company_info}, 관심 직무: {job_interest} "
        elif interview_type == "인성면접":
            question_prompt = f"{persona} 다음 정보를 바탕으로 IT 기업의 인성면접에서 물어볼 수 있는 질문을 생성해주세요. 질문은 한 문장으로, 직접적이고 명확하게 만들어주세요. 예를 들어, 개인 인성, 직무역량, 회사/직무/조직생활 관련 질문 등에 관한 질문을 하면 됩니다. 특히 지원하는 회사의 특성을 반영하여 질문을 생성해주세요: 지원자 프로필: {user_profile}, 회사 정보: {company_info}, 관심 직무: {job_interest}  "
        elif interview_type == "자기소개서 기반 면접":
            question_prompt = f"{persona} 다음 정보를 바탕으로 IT 기업의 자기소개서 기반 면접에서 물어볼 수 있는 질문을 생성해주세요. 질문은 한 문장으로, 직접적이고 명확하게 만들어주세요. 특히 자기소개서에 언급된 내용에 대한 질문만을 생성해주세요: 지원자 프로필: {user_profile}, 회사 정보: {company_info}, 관심 직무: {job_interest}, 자기소개서: {resume}  질문을 하나만 생성하고, 추가적인 행동을 하지 마세요."
        else:
            raise ValueError("면접 유형은 '기술면접', '인성면접', '자기소개서 기반 면접' 중에서 선택해야 합니다.")

        if interview_atmosphere == "압박 면접" and context:
            question_prompt += f"이전 질문들과 답변을 고려하여 추가적인 설명이 필요하거나 모순되는 부분을 파고드는 질문을 생성해야 합니다. 이전 질문과 답변: {context}"

        question = agent.invoke(question_prompt)

        # 에이전트의 최종 답변에서 실제 질문 추출
        if "질문:" in question:
            question = question.split("질문:")[1].strip()
        elif "Final Answer:" in question:
            question = question.split("Final Answer:")[1].strip()

        # provide_ai_response(f"질문 {i + 1}: {question}")

        # 사용자의 답변 받기
        answer = get_user_input("답변해 주세요: ", speech=True)

        # 압박 면접일 경우 컨텍스트 업데이트
        if interview_atmosphere == "압박 면접":
            context += f"질문 {i + 1}: {question}\n답변: {answer}\n"

        # 답변 평가
        evaluation_prompt = f"{persona} 다음 질문과 답변을 평가해주세요. 전체적인 답변의 퀄리티와 질문에 대한 적절성을 고려하여 평가해주세요: 질문: {question}, 답변: {answer}  평가를 한 번만 하고, 추가적인 행동이나 질문을 하지 마세요."
        evaluation = agent.invoke(evaluation_prompt)
        review.append(evaluation)

        provide_ai_response("답변 감사합니다. 다음 질문으로 넘어가겠습니다.")

    # 면접 종료 및 리뷰 제공
    provide_ai_response("면접 시뮬레이션이 끝났습니다. 다음은 각 답변에 대한 평가입니다:")
    for i, eval_result in enumerate(review, 1):
        provide_ai_response(f"질문 {i}에 대한 평가: {eval_result}")

    provide_ai_response("면접 준비에 많은 도움이 되셨기를 바랍니다!")


# 시뮬레이션 실행
if __name__ == "__main__":
    interview_simulation()