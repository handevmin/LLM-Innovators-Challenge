import os
from dotenv import load_dotenv
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.agents import Tool, create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory

import speech_recognition as sr
import pyttsx3
from typing import Any

# 환경 변수 로드
load_dotenv()

# Upstage API 키 설정
upstage_api_key = os.getenv("UPSTAGE_API_KEY")
if not upstage_api_key:
    raise ValueError("UPSTAGE_API_KEY not found in .env file.")
os.environ["UPSTAGE_API_KEY"] = upstage_api_key

# 임베딩 및 벡터 저장소 초기화
embeddings = UpstageEmbeddings(model="solar-embedding-1-large-passage", dimensions=1536)
vectorstore = Chroma(persist_directory="./knowledge_base", embedding_function=embeddings)

# LLM 초기화
llm = ChatUpstage(
    temperature=0.5,
    model_name="solar-1-mini-chat",
)

# 검색 기반 QA 체인 생성
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())


# Tools 정의
class InterviewQuestionGenerator(BaseTool):
    name: str = "Interview Question Generator"
    description: str = "Generates personalized job interview questions based on given user profile, company information, and job interests. The interview questions must be in Korean."

    def _run(self, query: str) -> str:
        prompt = f"Please create a job interview question based on the following information: {query}. Please create the question in Korean."
        return llm.invoke(prompt)

    def _arun(self, query: str) -> Any:
        raise NotImplementedError("This tool does not support async execution.")


class InterFeedbackGenerator(BaseTool):
    name: str = "User Response Feedback Generator"
    description: str = "Evaluates how well the user answered the interview questions and provides feedback. The feedback must be in Korean."

    def _run(self, query: str) -> str:
        return llm.invoke(query)

    def _arun(self, query: str) -> Any:
        raise NotImplementedError("This tool does not support async execution.")


question_generator = InterviewQuestionGenerator()
interview_feedback_generator = InterFeedbackGenerator()

# 메모리 초기화
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# 다중 Agents
class SpecialistAgent:
    def __init__(self, name, tools, memory):
        self.name = name
        template = """
        You're a professional job interviewer specializing in {name}.
        Based on the given company information and the candidate's profile, you {task}.
        Answer the following questions as best as you can. You have access to the following tools:

        {tools}

        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat 3 times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        ```Examples```
        [Example 1]
        Question: "Please search for information about 네이버. If no information is available, please provide information about a typical IT company.
        Thought: I should search for information about 네이버.
        Action: Company Information Searcher
        Action Input: "네이버"
        Observation: 네이버는 한국의 대표적인 IT 기업 중 하나로, 검색 엔진과 앱, 다양한 서비스 등을 제공한다.
        Thought: I now know the final answer
        Final Answer: 네이버는 한국의 대표적인 IT 기업 중 하나로, 검색 엔진과 앱, 다양한 서비스 등을 제공한다.

        [Example 2]
        Question: You are a professional job interviewer with following personality: You're a friendly, easygoing job interviewer. Ask questions in a friendly tone of voice to help the interviewee feel comfortable answering.

                Based on the given information, please generate specific and relevant interview questions that you might ask in a technical interview at an IT company. 
                Please keep your questions to one sentence, direct and clear.

                The question should especially be closely related to the "job of interest" given from the user. 
                The question must be in Korean.

                Information:
                Candidate profile: 인턴 경험 2회, 고려대학교 데이터과학과 학사, 파이썬 SQL R
                company information: 네이버
                job of interest: 데이터 엔지니어
        Thought: I should generate a specific and relevant interview question related to 데이터과학, 파이써, SQL, R, 네이버, 데이터 엔지니어.
        Action: Question Generator
        Action Input: "인턴 경험 2회, 고려대학교 데이터과학과 학사, 파이썬 SQL R, 네이버, 데이터 엔지니어"
        Observation: 데이터 엔지니어로 지원한 지원자에게 다음과 같은 질문을 할 수 있습니다: "파이썬과 SQL을 사용하여 어떤 프로젝트를 수행했나요?"
        Thought: I now know the final answer
        Final Answer: "파이썬과 SQL을 사용하여 어떤 프로젝트를 수행했나요?"

        [Example 3]
        Question: You're a sharp, thorough, and critical job interviewer. You find out all the inconsistencies and parts that need further clarification in the interviewee's answers.
            As a professional job interviewer, evaluate the user answer to the interview question.
            When evaluating, consider both the overall quality of the answer and its relevance to the question.
            It is important to give a non-biased and objective comment for the user, giving helpful solutions to improve user's interview skill. 
            The comment must be in Korean.

            Question: "파이썬과 SQL을 사용하여 어떤 프로젝트를 수행했나요?"
            Answer: "파이썬과 SQL을 사용한 프로젝트 중 하나는 데이터 파이프라인 구축과 관련된 작업이었습니다. 주로 데이터를 추출, 변환, 적재(ETL)하는 프로세스를 자동화하는 프로젝트였는데, 다양한 소스에서 데이터를 수집하여 분석에 적합한 형태로 변환한 후, 데이터베이스에 저장하는 작업이었습니다.
                    예를 들어, 파이썬의 pandas 라이브러리와 SQL을 결합하여 여러 CSV 파일에서 데이터를 읽고, 특정 비즈니스 로직에 따라 데이터 정제와 변환을 수행했습니다. 이 과정에서 중복 제거, 결측값 처리, 데이터 타입 변환 등의 작업을 했으며, 변환된 데이터를 MySQL 데이터베이스에 저장했습니다.
                    또한, 데이터베이스와 연동된 API를 개발하여 특정 조건에 맞는 데이터를 실시간으로 가져오고 분석할 수 있도록 했습니다. SQL 쿼리를 최적화하고 인덱싱을 사용하여 조회 성능을 개선한 경험도 있으며, 파이썬을 통해 데이터 흐름을 자동화하는 스크립트를 작성하여, 데이터 수집과 분석을 주기적으로 실행되도록 했습니다. 이 프로젝트를 통해 데이터 처리의 효율성을 크게 높일 수 있었고, 분석팀의 작업 속도를 개선할 수 있었습니다."
        Thought: I should evaluate the user's answer to the interview question.
        Action: User Answer Feedback Generator
        Action Input: "파이썬과 SQL을 사용한 프로젝트 중 하나는 데이터 파이프라인 구축과 관련된 작업이었습니다. 주로 데이터를 추출, 변환, 적재(ETL)하는 프로세스를 자동화하는 프로젝트였는데, 다양한 소스에서 데이터를 수집하여 분석에 적합한 형태로 변환한 후, 데이터베이스에 저장하는 작업이었습니다.
                    예를 들어, 파이썬의 pandas 라이브러리와 SQL을 결합하여 여러 CSV 파일에서 데이터를 읽고, 특정 비즈니스 로직에 따라 데이터 정제와 변환을 수행했습니다. 이 과정에서 중복 제거, 결측값 처리, 데이터 타입 변환 등의 작업을 했으며, 변환된 데이터를 MySQL 데이터베이스에 저장했습니다.
                    또한, 데이터베이스와 연동된 API를 개발하여 특정 조건에 맞는 데이터를 실시간으로 가져오고 분석할 수 있도록 했습니다. SQL 쿼리를 최적화하고 인덱싱을 사용하여 조회 성능을 개선한 경험도 있으며, 파이썬을 통해 데이터 흐름을 자동화하는 스크립트를 작성하여, 데이터 수집과 분석을 주기적으로 실행되도록 했습니다. 이 프로젝트를 통해 데이터 처리의 효율성을 크게 높일 수 있었고, 분석팀의 작업 속도를 개선할 수 있었습니다."
        Observation: "이 답변은 파이썬과 SQL을 사용한 프로젝트 경험을 상세하게 설명하고 있으며, ETL(추출, 변환, 적재) 과정과 관련된 구체적인 작업 내용을 포함하고 있어 전반적으로 좋은 인상을 줍니다. 특히, pandas 라이브러리와 SQL의 결합, 데이터 정제 및 변환 작업, 데이터베이스 연동과 쿼리 최적화 경험을 언급한 점은 기술적 깊이를 보여주고 있습니다. 또한, 자동화 스크립트를 작성하여 데이터 처리 과정을 효율화했다는 부분도 문제 해결 능력과 실무에 기여한 바를 잘 설명하고 있습니다.

                        하지만 답변을 더욱 개선할 수 있는 몇 가지 요소가 있습니다:

                        1. 프로젝트의 목표와 결과: 프로젝트의 목표가 무엇이었고, 이를 통해 어떤 구체적인 성과를 얻었는지 더 명확히 설명하면 좋겠습니다. 예를 들어, "데이터 처리의 효율성을 높였다"는 부분을 좀 더 구체화하여, 얼마만큼의 성능 개선이 있었는지 또는 분석팀의 작업 속도가 몇 퍼센트 향상되었는지 등 구체적인 수치나 예시를 들어주면 더 설득력 있을 것입니다.

                        2. SQL 쿼리 최적화와 인덱싱 경험: SQL 쿼리 최적화와 인덱싱 작업이 무엇을 해결했는지에 대한 설명이 부족합니다. 예를 들어, 쿼리 실행 시간이 어떻게 개선되었는지, 인덱싱을 통해 조회 성능이 얼마나 향상되었는지를 설명하면 더 좋을 것입니다.

                        3. 실시간 데이터 처리: 실시간 데이터를 처리하는 API 개발 경험을 언급했지만, 실시간 처리의 필요성이나 도전 과제가 무엇이었고, 이를 어떻게 해결했는지에 대한 추가 설명이 있으면 더 좋습니다.

                        4. 팀워크와 협업: 프로젝트에서 다른 팀원들과 어떻게 협업했는지, 또는 프로젝트에서 맡은 역할이 무엇이었는지에 대한 설명이 부족합니다. 특히 분석팀과의 협업을 통해 어떻게 성과를 냈는지에 대한 구체적인 사례를 제시하면 답변이 더욱 풍부해질 것입니다.

                        종합적으로, 답변은 전반적으로 기술적인 경험을 잘 설명하고 있으나, 프로젝트의 목표와 성과, 구체적인 개선 사항, 그리고 협업 과정에 대한 추가 설명이 필요합니다. 이를 보완하면 더욱 강력하고 설득력 있는 답변이 될 것입니다."
        Thought: I now know the final answer
        Final Answer: 이 답변은 파이썬과 SQL을 사용한 프로젝트 경험을 상세하게 설명하고 있으며, ETL(추출, 변환, 적재) 과정과 관련된 구체적인 작업 내용을 포함하고 있어 전반적으로 좋은 인상을 줍니다. 특히, pandas 라이브러리와 SQL의 결합, 데이터 정제 및 변환 작업, 데이터베이스 연동과 쿼리 최적화 경험을 언급한 점은 기술적 깊이를 보여주고 있습니다. 또한, 자동화 스크립트를 작성하여 데이터 처리 과정을 효율화했다는 부분도 문제 해결 능력과 실무에 기여한 바를 잘 설명하고 있습니다.

                        하지만 답변을 더욱 개선할 수 있는 몇 가지 요소가 있습니다:

                        1. 프로젝트의 목표와 결과: 프로젝트의 목표가 무엇이었고, 이를 통해 어떤 구체적인 성과를 얻었는지 더 명확히 설명하면 좋겠습니다. 예를 들어, "데이터 처리의 효율성을 높였다"는 부분을 좀 더 구체화하여, 얼마만큼의 성능 개선이 있었는지 또는 분석팀의 작업 속도가 몇 퍼센트 향상되었는지 등 구체적인 수치나 예시를 들어주면 더 설득력 있을 것입니다.

                        2. SQL 쿼리 최적화와 인덱싱 경험: SQL 쿼리 최적화와 인덱싱 작업이 무엇을 해결했는지에 대한 설명이 부족합니다. 예를 들어, 쿼리 실행 시간이 어떻게 개선되었는지, 인덱싱을 통해 조회 성능이 얼마나 향상되었는지를 설명하면 더 좋을 것입니다.

                        3. 실시간 데이터 처리: 실시간 데이터를 처리하는 API 개발 경험을 언급했지만, 실시간 처리의 필요성이나 도전 과제가 무엇이었고, 이를 어떻게 해결했는지에 대한 추가 설명이 있으면 더 좋습니다.

                        4. 팀워크와 협업: 프로젝트에서 다른 팀원들과 어떻게 협업했는지, 또는 프로젝트에서 맡은 역할이 무엇이었는지에 대한 설명이 부족합니다. 특히 분석팀과의 협업을 통해 어떻게 성과를 냈는지에 대한 구체적인 사례를 제시하면 답변이 더욱 풍부해질 것입니다.

                        종합적으로, 답변은 전반적으로 기술적인 경험을 잘 설명하고 있으나, 프로젝트의 목표와 성과, 구체적인 개선 사항, 그리고 협업 과정에 대한 추가 설명이 필요합니다. 이를 보완하면 더욱 강력하고 설득력 있는 답변이 될 것입니다."
        ```Examples End```                        

        IMPORTANT : 
        1) NEVER output both a parse-able action and a final answer at the same time
        2) Once returning the first 'Final Answer', you MUST STOP the process, including every Thought, Action, and Action Input. It is very important that you DIRECTLY RETURN the very first Final Answer you get. 
        3) The name of each process of ReAct must be written in English i.e. 'Thought: ', 'Action:', 'Action Input:', 'Observation: ', 'Final Answer: '. 

        Begin!

        Question: {input}
        Thought: {agent_scratchpad}
        """
        prompt = PromptTemplate.from_template(template).partial(name=name, task=self.get_task(name))
        self.agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=tools, verbose=True, max_iterations=5,
                                            memory=memory,
                                            handle_parsing_errors="Check your output and make sure it conforms! Do not output an action and a final answer at the same time. Once returning a single 'Final Answer', stop the process and return the final answer. Don't do anything else.")

    def get_task(self, name):
        if name == "Company":
            return "search for company information"
        elif name == "Question":
            return "generate appropriate interview questions"
        elif name == "Feedback":
            return "evaluate the user answers"
        else:
            return "perform your specialized task"

    def run(self, query):
        return self.agent_executor.invoke({"input": query})["output"]


company_agent = SpecialistAgent("Company", [
    Tool(name="Company Information Searcher", func=qa.run, description="Searches for information about the company")],
                                memory)
question_agent = SpecialistAgent("Question", [Tool(name="Question Generator", func=question_generator._run,
                                                   description="Generates job interview questions in Korean")], memory)
feedback_agent = SpecialistAgent("Feedback", [
    Tool(name="User Answer Feedback Generator", func=interview_feedback_generator._run,
         description="Evaluate user answers to the interview question and provide feedback")], memory)

# Set up speech recognition and synthesis
recognizer = sr.Recognizer()
engine = pyttsx3.init()


def setup_tts():
    voices = engine.getProperty('voices')
    for voice in voices:
        if "korean" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 150)


setup_tts()


def get_user_input(query, speech=False):
    if speech:
        with sr.Microphone() as source:
            print(query)
            engine.say(query)
            engine.runAndWait()
            print("말씀해 주세요...")
            audio = recognizer.listen(source)
            try:
                user_input = recognizer.recognize_google(audio, language="ko-KR")
                print(f"인식된 음성: {user_input}")
                return user_input
            except sr.UnknownValueError:
                print("죄송합니다. 음성을 인식하지 못했습니다. 다시 시도해 주세요.")
                return get_user_input(query, speech)
            except sr.RequestError:
                print("음성 인식 서비스에 접근할 수 없습니다. 텍스트로 입력해 주세요.")
                return input(query)
    else:
        return input(query)


def provide_ai_response(response, speech=False):
    print(response)
    if speech:
        engine.say(response)
        engine.runAndWait()


def interview_simulation():
    # 사용자 프로필
    # user_profile = get_user_input("귀하의 프로필을 입력해주세요 (경력, 학력, 기술 스택 등): ", speech=False)
    user_profile = "인턴 경험 2회, 고려대학교 데이터과학과 학사, 파이썬 SQL R"

    # 목표 회사
    # company_name = get_user_input("어느 회사에 지원하시나요? ", speech=False)
    company_name = "네이버"

    # 관심 직무
    # job_interest = input("어떤 직무에 관심이 있으신가요?: ")
    job_interest = "데이터 엔지니어"

    # 면접 유형
    # interview_type = input("면접 유형을 선택해주세요 (기술면접, 인성면접, 자기소개서 기반 면접): ")
    interview_type = "기술면접"

    coverletter = ""
    if interview_type == "자기소개서 기반 면접":
        coverletter = input("자기소개서를 입력해주세요: ")

    # 면접 분위기
    # interview_atmosphere = input("면접 분위기를 선택해주세요 (일반 면접, 압박 면접): ")
    interview_atmosphere = "일반 면접"

    # 면접관 persona 설정
    if interview_atmosphere == "일반 면접":
        persona = "You're a friendly, easygoing job interviewer. Ask questions in a friendly tone of voice to help the interviewee feel comfortable answering."
    elif interview_atmosphere == "압박 면접":
        persona = "You're a sharp, thorough, and critical job interviewer. You dig in and ask questions, focusing on inconsistencies in the interviewee's answers or areas that need further clarification."
    else:
        raise ValueError("면접 분위기는 '일반 면접' 또는 '압박 면접' 중에서 선택해야 합니다.")

    # 회사 정보 검색
    company_info_prompt = f"Please search for information about {company_name}. If no information is available, please provide information about a typical IT company."
    company_info = company_agent.run(company_info_prompt)

    review = []
    context = ""

    num_questions = int(input("면접 질문 수를 입력해주세요: "))
    for i in range(num_questions):
        if interview_type == "기술면접":
            question_prompt = f"""
                You are a professional job interviewer with following personality: {persona} 

                Based on the given information, please generate specific and relevant interview questions that you might ask in a technical interview at an IT company. 
                Please keep your questions to one sentence, direct and clear.

                The question should especially be closely related to the "job of interest" given from the user. 
                The question must be in Korean.

                Information:
                Candidate profile: {user_profile}
                company information: {company_info}
                job of interest: {job_interest} 
            """

        elif interview_type == "인성면접":
            question_prompt = f"""
                You are a professional job interviewer with following personality: {persona} 

                Based on the given information, please generate specific and relevant interview questions that you might ask in a Fit Interview at an IT company. 
                For example, you can ask questions about the user's personality, job skills, or company/job/organizational life, etc.
                Please keep your questions to one sentence, direct and clear.

                The question should especially be closely related to the "company information". 
                The question must be in Korean.

                Information:
                Candidate profile: {user_profile}
                company information: {company_info}
                job of interest: {job_interest} 
            """

        elif interview_type == "자기소개서 기반 면접":
            question_prompt = f"""
                You are a professional job interviewer with following personality: {persona} 

                Based on the given information, please generate specific and relevant interview questions that you might ask in a coverletter-based interview at an IT company. 

                Please keep your questions to one sentence, direct and clear.

                The question should especially be closely related to the "Coverletter". 
                The question must be in Korean.

                Information:
                Candidate profile: {user_profile}
                company information: {company_info}
                job of interest: {job_interest} 
                Coverletter: {coverletter}
            """
        else:
            raise ValueError("면접 유형은 '기술면접', '인성면접', '자기소개서 기반 면접' 중에서 선택해야 합니다.")

        if interview_atmosphere == "압박 면접" and context:
            question_prompt += f"""
                Consider the previously created interview questions and user's answers to that questions.
                Your question must be based on them, probing for additional clarification or pointing out contradictions in the user's previous answers.

                Previous questions and answers: {context}
            """

        question = question_agent.run(question_prompt)

        provide_ai_response(f"질문 {i + 1}: {question}")

        # 사용자 답변 받기
        answer = get_user_input("답변해 주세요: ", speech=False)

        # 압박 면접일 경우 context 업데이트
        if interview_atmosphere == "압박 면접":
            context += f"Question {i + 1}: {question}\nAnswer {i + 1}: {answer}\n"

        # 답변 평가
        evaluation_prompt = f"""
            You're a sharp, thorough, and critical job interviewer. You find out all the inconsistencies and parts that need further clarification in the interviewee's answers.
            As a professional job interviewer, evaluate the user answer to the interview question.
            When evaluating, consider both the overall quality of the answer and its relevance to the question.
            It is important to give a non-biased and objective comment for the user, giving helpful solutions to improve user's interview skill. 
            The comment must be in Korean.

            Question: {question}
            Answer: {answer}
        """

        evaluation = feedback_agent.run(evaluation_prompt)
        review.append(evaluation)

        provide_ai_response("답변 감사합니다. 다음 질문으로 넘어가겠습니다.")

    provide_ai_response("면접 시뮬레이션이 끝났습니다. 다음은 각 답변에 대한 평가입니다:")
    for i, eval_result in enumerate(review, 1):
        provide_ai_response(f"질문 {i}에 대한 평가: {eval_result}")

    # 면접 종료 및 평가 제공
    provide_ai_response("면접 준비에 많은 도움이 되셨기를 바랍니다!")


if __name__ == "__main__":
    interview_simulation()