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
import json
from typing import Any

# 환경 변수 로드
load_dotenv()

# Upstage API 키 설정
upstage_api_key = os.getenv("UPSTAGE_API_KEY")
if not upstage_api_key:
    raise ValueError("UPSTAGE_API_KEY not found in .env file.")
os.environ["UPSTAGE_API_KEY"] = upstage_api_key

# 임베딩 및 벡터 저장소 초기화
embeddings = UpstageEmbeddings(model="solar-embedding-1-large-passage")
vectorstore = Chroma(persist_directory="./knowledge_base_upstage", embedding_function=embeddings)

# LLM 초기화
llm = ChatUpstage(
    temperature=0.5,
    model_name="solar-1-mini-chat",
)

# 번역 모델 초기화
translator_en_ko = ChatUpstage(
    temperature=0.1,
    model_name="solar-1-mini-translate-enko",
)

translator_ko_en = ChatUpstage(
    temperature=0.1,
    model_name="solar-1-mini-translate-koen",
)

# 검색 기반 QA 체인 생성
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())


# Tools 정의
class InterviewQuestionGenerator(BaseTool):
    name: str = "Interview Question Generator"
    description: str = "Generates personalized job interview questions based on given user profile, company information, and job interests."

    def _run(self, query: str) -> str:
        return llm.invoke(query)

    def _arun(self, query: str) -> Any:
        raise NotImplementedError("This tool does not support async execution.")


class InterFeedbackGenerator(BaseTool):
    name: str = "User Response Feedback Generator"
    description: str = "Evaluates how well the user answered the interview questions and provides feedback."

    def _run(self, query: str) -> str:
        return llm.invoke(query)

    def _arun(self, query: str) -> Any:
        raise NotImplementedError("This tool does not support async execution.")


class Translator(BaseTool):
    name: str = "Translator"
    description: str = "Translates text between Korean and English."

    def _run(self, query: str) -> str:
        text, direction = query.split('|')
        if direction == 'ko_to_en':
            return translator_ko_en.invoke(text)
        elif direction == 'en_to_ko':
            return translator_en_ko.invoke(text)
        else:
            raise ValueError("Invalid translation direction. Use 'ko_to_en' or 'en_to_ko'.")

    def _arun(self, query: str) -> Any:
        raise NotImplementedError("This tool does not support async execution.")


question_generator = InterviewQuestionGenerator()
interview_feedback_generator = InterFeedbackGenerator()
translator = Translator()

# 메모리 초기화
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# 다중 Agents
class SpecialistAgent:
    def __init__(self, name, tools, memory):
        self.name = name
        template = """
        You're a professional job interviewer specializing in {name}.
        Based on the given information, you {task}.
        Answer the following questions as best as you can. You have access to the following tools: {tools}

        Follow the instructions carefully and provide the best possible answers.

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action

        Final Thought: I now know the final answer
        Final Answer: the final answer to the original input question


        ```Examples```
        [Example 1]
        Question: "Please search for information about 네이버. If no information is available, please provide information about a typical IT company.
        Thought: I should search for information about 네이버.
        Action: Company Information Searcher
        Action Input: 네이버
        Observation: 네이버 is a leading South Korean IT company, known for services like its search engine, Line messenger, AI, and cloud platforms. Key departments include R&D (backend, frontend, AI), service planning, UX/UI design, business development, and Naver Cloud. Naver seeks innovative talent in both technical and non-technical areas, emphasizing creativity and problem-solving. They value expertise in areas like AI, big data, and user experience.,

        Final Thought: I now know the final answer
        Final Answer: 네이버 is a leading South Korean IT company, known for services like its search engine, Line messenger, AI, and cloud platforms. Key departments include R&D (backend, frontend, AI), service planning, UX/UI design, business development, and Naver Cloud. Naver seeks innovative talent in both technical and non-technical areas, emphasizing creativity and problem-solving. They value expertise in areas like AI, big data, and user experience.

        [Example 2]
        Question: You are a professional job interviewer with following personality: You're a friendly, easygoing job interviewer. Ask questions in a friendly tone of voice to help the interviewee feel comfortable answering.

                Based on the given information, please generate specific and relevant interview questions that you might ask in a technical interview at an IT company. 
                Please keep your questions to one sentence, direct and clear.

                The question should especially be closely related to the "job of interest" given from the user. 
                The question must be in Korean.

                Information:
                Candidate profile: 2 internships, B.S. in Data Science, Korea University, Python SQL R
                company information: 네이버
                job of interest: Data Engineering
        Thought: I should generate a specific and relevant interview question related to 2 internships, B.S. in Data Science, Korea University, Python SQL , 네이버, Data Engineering
        Action: Question Generator
        Action Input: 2 internships, B.S. in Data Science, Korea University, Python SQL R, 네이버, Data Engineering
        Observation: I could ask the interviewee who has applied for a data engineer position questions such as “What projects have you worked on using Python and SQL?”

        Final Thought: I now know the final answer
        Final Answer: “What projects have you worked on using Python and SQL?”

        [Example 3]
        Question: You're a sharp, thorough, and critical job interviewer. You find out all the inconsistencies and parts that need further clarification in the interviewee's answers.
            As a professional job interviewer, evaluate the user answer to the interview question.
            When evaluating, consider both the overall quality of the answer and its relevance to the question.
            It is important to give a non-biased and objective comment for the user, giving helpful solutions to improve user's interview skill. 
            The comment must be in Korean.

            Question: “What projects have you worked on using Python and SQL?”
            Answer: "One of the projects I worked on using Python and SQL involved building a data pipeline. It was primarily a project to automate the process of extracting, transforming, and loading (ETL) data, which involved collecting data from various sources, transforming it into a form suitable for analysis, and storing it in a database.
                    For example, we combined Python's pandas library with SQL to read data from multiple CSV files, perform data cleansing and transformation based on specific business logic, including deduplication, missing value handling, and data type conversion, and store the transformed data in a MySQL database.
                    We also developed an API to work with the database, allowing us to pull and analyze data in real-time for specific conditions. I have experience optimizing SQL queries and using indexing to improve lookup performance, and I wrote scripts to automate data flow through Python, ensuring that data collection and analysis are run periodically. This project has greatly increased the efficiency of data processing and helped speed up the work of the analytics team."
        Thought: I should evaluate the user's answer to the interview question.
        Action: User Answer Feedback Generator
        Action Input: "One of the projects I worked on using Python and SQL involved building a data pipeline. It was primarily a project to automate the process of extracting, transforming, and loading (ETL) data, which involved collecting data from various sources, transforming it into a form suitable for analysis, and storing it in a database.
                    For example, we combined Python's pandas library with SQL to read data from multiple CSV files, perform data cleansing and transformation based on specific business logic, including deduplication, missing value handling, and data type conversion, and store the transformed data in a MySQL database.
                    We also developed an API to work with the database, allowing us to pull and analyze data in real-time for specific conditions. I have experience optimizing SQL queries and using indexing to improve lookup performance, and I wrote scripts to automate data flow through Python, ensuring that data collection and analysis are run periodically. This project has greatly increased the efficiency of data processing and helped speed up the work of the analytics team."
        Observation: "This answer gives a good impression as it details your project experience using Python and SQL, and includes specific tasks related to the extract, transform, and load (ETL) process. In particular, your mention of combining the pandas library with SQL, working with data cleansing and transformation, and experience with database integration and query optimization demonstrates your technical depth. In addition, your mention of writing automation scripts to streamline data processing demonstrates your problem-solving skills and practical contributions.

                        However, there are a few elements that could improve your answer even further:

                        1. the goals and outcomes of the project: You could be more explicit about what the goals of the project were and what specific outcomes you achieved. For example, “I made data processing more efficient” would be more compelling if you could be more specific and provide specific numbers or examples, such as how much performance improvement you achieved or what percentage the analytics team was able to work faster.

                        2. SQL query optimization and indexing experience: The description of what the SQL query optimization and indexing work solved is lacking. For example, it would be better to explain how query execution time was improved, or how indexing improved lookup performance.

                        3. Real-time data processing: You mentioned your experience developing APIs that process real-time data, but it would be great to see more explanation of what the need or challenge was for real-time processing and how you addressed it.

                        4. Teamwork and collaboration: There is a lack of explanation of how you collaborated with other team members on the project or what your role was in the project. Your answer would be enriched by providing specific examples of how you collaborated with the analytics team in particular to achieve results.

                        Overall, your answer describes your technical experience well, but needs further explanation of the project's goals and outcomes, specific improvements, and the collaborative process. This would make your answer stronger and more compelling."

        Final Thought: I now know the final answer
        Final Answer: This answer gives a good impression as it details your project experience using Python and SQL, and includes specific tasks related to the extract, transform, and load (ETL) process. In particular, your mention of combining the pandas library with SQL, working with data cleansing and transformation, and experience with database integration and query optimization demonstrates your technical depth. In addition, your mention of writing automation scripts to streamline data processing demonstrates your problem-solving skills and practical contributions.

                        However, there are a few elements that could improve your answer even further:

                        1. the goals and outcomes of the project: You could be more explicit about what the goals of the project were and what specific outcomes you achieved. For example, “I made data processing more efficient” would be more compelling if you could be more specific and provide specific numbers or examples, such as how much performance improvement you achieved or what percentage the analytics team was able to work faster.

                        2. SQL query optimization and indexing experience: The description of what the SQL query optimization and indexing work solved is lacking. For example, it would be better to explain how query execution time was improved, or how indexing improved lookup performance.

                        3. Real-time data processing: You mentioned your experience developing APIs that process real-time data, but it would be great to see more explanation of what the need or challenge was for real-time processing and how you addressed it.

                        4. Teamwork and collaboration: There is a lack of explanation of how you collaborated with other team members on the project or what your role was in the project. Your answer would be enriched by providing specific examples of how you collaborated with the analytics team in particular to achieve results.

                        Overall, your answer describes your technical experience well, but needs further explanation of the project's goals and outcomes, specific improvements, and the collaborative process. This would make your answer stronger and more compelling.
        ```Examples End```  


        IMPORTANT : 
        1) NEVER output both a parse-able action and a final answer at the same time
        2) Once returning the first 'Final Answer', you MUST STOP the process, including every Thought, Action, and Action Input. It is very important that you DIRECTLY RETURN the very first Final Answer you get. 
        3) When creating output, NEVER create the same or similar output you've created before. Always create a new unique output.

        Begin!

        Query: {input}
        Thought: {agent_scratchpad}
        """
        prompt = PromptTemplate.from_template(template).partial(name=name, task=self.get_task(name))
        self.agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            memory=memory,
            handle_parsing_errors="Check your output and make sure it conforms! Only output the Final Answer."
        )

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
    Tool(name="Company Information Searcher", func=qa.run, description="Searches for information about the company"),
    Tool(name="Translator", func=translator._run, description="Translates text between Korean and English")], memory)
question_agent = SpecialistAgent("Question", [
    Tool(name="Question Generator", func=question_generator._run, description="Generates job interview questions"),
    Tool(name="Translator", func=translator._run, description="Translates text between Korean and English")], memory)
feedback_agent = SpecialistAgent("Feedback", [
    Tool(name="User Answer Feedback Generator", func=interview_feedback_generator._run,
         description="Evaluate user answers to the interview question and provide feedback"),
    Tool(name="Translator", func=translator._run, description="Translates text between Korean and English")], memory)

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


"""
def provide_ai_response(response, speech=False):
    print(response)
    if speech:
        engine.say(response)
        engine.runAndWait()
"""


def provide_ai_response(response, speech=False):
    cleaned_response = extract_translation_content(response)
    print(cleaned_response)
    if speech:
        engine.say(cleaned_response)
        engine.runAndWait()


def extract_translation_content(response):
    try:
        # response가 문자열인 경우 (JSON 형식)
        if isinstance(response, str):
            response_dict = json.loads(response)
            return response_dict.get('content', '').strip('"')
        # response가 이미 딕셔너리인 경우
        elif isinstance(response, dict):
            return response.get('content', '').strip('"')
        # response가 ChatUpstage 객체인 경우
        elif hasattr(response, 'content'):
            return response.content.strip('"')
        else:
            return str(response)
    except json.JSONDecodeError:
        # JSON 파싱에 실패한 경우, 원본 문자열 반환
        return response.strip('"')


# 번역
def translate(text, direction):
    translated = translator._run(f"{text}|{direction}")
    return extract_translation_content(translated)


def map_interview_type(korean_type):
    mapping = {
        "기술면접": "technical interview",
        "인성면접": "behavioral interview",
        "자기소개서 기반 면접": "coverletter-based interview"
    }
    return mapping.get(korean_type, "unknown interview type")


def map_interview_atmosphere(korean_atmosphere):
    mapping = {
        "일반 면접": "general interview",
        "압박 면접": "pressure interview",
        "편안한 면접": "comfortable interview"
    }
    return mapping.get(korean_atmosphere, "unknown interview atmosphere")

def interview_simulation():
    # user_profile = translate(get_user_input("귀하의 프로필을 입력해주세요 (경력, 학력, 기술 스택 등): ", speech=False), "ko_to_en")
    # company_name = get_user_input("어느 회사에 지원하시나요? ", speech=False)
    # job_interest = translate(get_user_input("어떤 직무에 관심이 있으신가요?: "), "ko_to_en")

    user_profile = "인하대학교 / 학점 3.56 / 토익스피킹 레벨 6(140) / 컴활 2급, 정보처리기능사, 한국사 1급, 2018년 학과 학생회장"
    company_name = "KT"
    job_interest = "AI/SW개발"

    interview_type_kor = get_user_input("면접 유형을 선택해주세요 (기술면접, 인성면접, 자기소개서 기반 면접): ")
    interview_type = map_interview_type(interview_type_kor)

    coverletter = """1. 자신에 대해 자유롭게 표현해주세요.

                        # 유니콘을 꿈꾸는 공대생

                        저는 실리콘밸리의 성공한 기업들을 보고 공학에 대한 매력을 느껴 이공계열로 진학하게 되었습니다. 그리고 혁신적인 로봇을 만들어 사람들에게 많은 도움을 주고 싶었기 때문에 기계공학을 전공하기로 결정했습니다. 하지만 학과 공부만으로는 주도적으로 제 아이디어를 실현하기는 어렵다고 생각했고, 로봇을 개발하기까지 많은 시간이 걸린다는 점이 아쉬웠습니다. 그래서 창업을 통해 빠르게 저만의 서비스를 만들어보려고 했습니다.

                        그때부터 스타트업에 관심을 가지고 스타트업 수업을 수강하면서 창업을 시작했습니다. 이후, 대학연합 실전창업학회에 들어가서 스타트업 대표님, VC 등의 현업에서 일하시는 분들과 교류하며 많은 깨달음을 얻었습니다. 특히 다양한 시도를 해보는 것이 중요하다는 것을 느꼈고, 이를 실천하기 위해 많은 서비스를 기획하여 사람을 모으고, 서비스를 제공해보았습니다. 그리고 그중 괜찮은 아이템으로 다시 창업을 시도해보았습니다.

                        # 배움을 즐기는 사람

                        여러 종류의 IT 서비스를 준비하면서 플랫폼, SNS, 펫, 긱 이코노미 등 많은 분야에 대해 배우게 되었습니다. 처음에는 제가 잘 모르는 분야의 서비스를 만드는 것에 대해 걱정이 되었지만, 해당 분야에 대해 공부하면서 문제를 파악하고 이를 해결할 수 있는 아이디어가 떠올랐습니다. 솔루션과 비즈니스 모델을 기존의 방식과 비교하고, 검증하며 새로운 가능성에 기대하게 되었고, 더 열심히 아이디어를 실현하고자 했습니다.

                        IT 서비스를 만들기 위해서 개발 역량이 필요하다고 판단하여 웹 개발을 배웠고, 취업사관학교 AI 과정도 수료했습니다. 그리고 해커톤에 나가서 개발자들과 짧은 시간 안에 결과를 도출했습니다. 또한 B2B 아이템을 진행하기 위해 콜드메일을 보내고, 기업 실무자와 대표까지 만나보면서 피드백을 받아 부족한 점을 보완하기 위해 노력했습니다. 자취방 청소 플랫폼 서비스를 제공하기 위해 직접 청소용품을 들고 가서 청소도 해보았고, 청소부를 구해 청소할 자취방을 배정했습니다.



                        2. 팀을 이뤄 협업을 하면서 성과를 이뤘던 경험을 적어주세요. 자신이 어떤 역할로 팀에 기여했고 어떤 교훈을 얻었는지를 포함해 주세요. (단, 학교 팀 과제를 수행한 경우는 제외)

                        # B2B 플랫폼 공동창업자

                        전기차 배터리 장비 견적 비교 플랫폼 ‘Preset’의 공동창업자로 6개월 동안 기술/영업 부분을 담당했습니다. 장비에 관한 정보를 찾아 내용을 정리하여 IR 자료를 제작했습니다. 그리고 B2B 사업을 위해 배터리 장비 제조업체들 리스트를 만들고, 제조업체에 가서 미팅을 진행했습니다. 그리고 전문가들의 피드백을 받으면서 내가 만들고 싶은 제품이 아니라, 시장이 원하는 제품을 만드는 것이 중요하다는 것을 깨달았습니다.

                        이후에 사업 계획에서 부족한 부분을 찾고, 최대한 고객의 입장에 초점을 두어 비즈니스 모델을 보완했습니다. 해당 아이템으로 2021년 성북구 청년 소셜벤처 혁신경연대회 우수상을 받았으며, 성북구 사회적 경제센터에 입주기업으로 선정되었습니다. 이를 통해 자신의 아이템을 너무 좋아해서, 객관적으로 바라보지 못하는 것을 경계해야겠다고 느꼈습니다. 아무리 좋은 아이디어라고 생각해도 한발 뒤로 물러나 부족한 점은 없는지 확인하는 절차를 밟고, 보완하며 아이템을 발전시켰습니다. 하지만 법적 위험이 있어 아쉽게도 결국 사업을 정리하게 되었고, 법적인 부분도 꼼꼼히 확인할 필요가 있다는 것을 알게 되었습니다.

                        # 펫 헬스케어 팀 대표

                        저는 반려견 슬개골탈구 예방/검진 서비스를 개발하는 ‘바른펫’의 팀장으로 기획부터 개발까지 참여했습니다. 여러 번의 창업 시도를 통해 저는 페인포인트를 해결할 수 있는 아이템을 만들고 싶어한다는 것을 느꼈습니다. 그래서 바른펫은 반려견은 아파도 아프다고 말할 수 없다는 페인포인트로 시작하였습니다. 혼자서 성장하는 펫 시장에 대해 조사하여 슬개골탈구 검진기 아이템을 기획하였고, 해당 아이템을 같이 개발할 고려대 사이버국방학과, 연세대 전기공학과 전공의 팀원을 모았습니다.

                        저는 기획, 기구 설계를 맡아 제품 개발을 진행하며 팀을 리드했고, 팀원들은 Arduino 개발과 Web 개발을 맡아서 같이 프로토타입을 제작했습니다. 반려견 슬개골탈구 예방/검진 서비스를 발표하여 고양산업진흥원 메이커톤에서 대상을 받았고, 서울과학기술대학교 창업지원단 메이커스페이스 해커톤에서 최우수상을 받았으며, 고려대 디지털 SW융합 콘텐츠 공모전 AI/빅데이터 분야 최우수상을 받았습니다. 또한 LINC3.0 KU창업동아리에 선정되어 제품 제작 지원을 받게 되었습니다. 

                        이후 팀의 AI 역량을 바탕으로 반려견 행동 데이터 분석을 진행하며 검진 정확도를 높이는 방향으로 아이템을 발전시키고자 했습니다. 그리고 동아일보 IT 기사에 나온 바른펫의 반려견 슬개골탈구 검진기 프로토타입을 보고, 라이펫 서비스를 만드는 ‘십일리터’ 대표님이 협업을 제안하셨습니다. 그래서 시제품 개발 이후, 네트워크를 쌓은 볼트앤너트를 통해 제조업체를 찾아 양산을 진행하고, 페토바이오에서 임상시험을 거쳐 인증과 특허를 취득할 계획을 수립했습니다. 이처럼 여러 번의 서비스 제작 시도를 하고, 기회를 얻기 위해 부딪히면서 도전하여 결과를 냈습니다. 이를 통해 끊임없이 도전해야 발전할 수 있다는 것을 느꼈습니다.
                    """
    # if interview_type.lower() == "coverletter-based interview":
    #    coverletter = translate(input("자기소개서를 입력해주세요: "), "ko_to_en")

    interview_atmosphere_kor = get_user_input("면접 분위기를 선택해주세요 (일반 면접, 압박 면접, 편안한 면접): ")
    interview_atmosphere = map_interview_atmosphere(interview_atmosphere_kor)

    if interview_atmosphere.lower() == "general interview":
        persona = "You're a friendly, easygoing job interviewer. Ask questions in a friendly tone of voice to help the interviewee feel comfortable answering."
    elif interview_atmosphere.lower() == "pressure interview":
        persona = "You're a sharp, thorough, and critical job interviewer. You dig in and ask questions, focusing on inconsistencies in the interviewee's answers or areas that need further clarification."
    elif interview_atmosphere.lower() == "comfortable interview":
        persona = "You're a supportive and encouraging job interviewer. Create a relaxed atmosphere and ask questions that allow the interviewee to showcase their strengths and experiences positively."
    else:
        raise ValueError("면접 분위기는 '일반 면접', '압박 면접' 또는 '편안한 면접' 중에서 선택해야 합니다.")

    company_info_prompt = f"Please search for information about {company_name}. If no information is available, please provide information about a typical IT company."
    company_info = company_agent.run(company_info_prompt)

    review = []
    context = ""

    generated_questions = []

    num_questions = int(input("면접 질문 수를 입력해주세요: "))

    for i in range(num_questions):
        if interview_type.lower() == "technical interview":
            question_prompt = f"""
                You are a professional job interviewer with following personality: {persona} 

                Based on the given information, please generate specific and relevant interview questions that you might ask in a Technical Interview at an IT company. 
                Please keep your questions to one sentence, direct and clear.

                The question should especially be closely related to the "job of interest" given from the user. 
                For instance, you can ask about specific information about one of the technology stacks mentioned in user_profile or projects related to the job of interest, etc.

                IMPORTANT. NEVER ASK QUESTION ASKING WHAT THE USER DID OR EXPERIENCED IN THE {company_info}". The user never worked in {company_info}.

                Information:
                Candidate profile: {user_profile}
                Target Company: {company_info}
                job of interest: {job_interest} 
            """

        elif interview_type.lower() == "behavioral interview":
            question_prompt = f"""
                You are a professional job interviewer with following personality: {persona} 

                Based on the given information, please generate specific and relevant interview questions that you might ask in a Behavioral Interview at a company. 
                For example, you can ask questions about the user's personality, job skills, or company/job/organizational life, etc.
                Please keep your questions to one sentence, direct and clear.

                Below are some examples of behavioral interview questions:
                ```Examples```
                    Tell me about a time when you had to work under pressure.
                    Describe a situation where you had to solve a difficult problem.
                    Tell me about the hardest experience of your life and how you got through it.
                    Explain why you chose this specific job.
                    Describe a situation where you had to work with a difficult team member and how you handled it.
                    How do you think would your coworkers describe you?
                    Which do you prefer: working alone or in a team? Why?
                    Describe the top 3 factors and priorities you look for when choosing a job.
                    Describe your strengths and weaknesses.
                    Explain how you would handle a big mistake of an employee (both as a coworker and as a boss) 
                    What do you value most in life?
                    Explain your own criteria for making decisions.
                    Describe how you handle conflict with your coworker or boss.
                ```Examples End```

                IMPORTANT. NEVER ASK QUESTION ASKING WHAT THE USER DID OR EXPERIENCED IN THE {company_info}". The user never worked in {company_info}.

                Information:
                Candidate profile: {user_profile}
                Target Company: {company_info}
                job of interest: {job_interest} 
            """

        elif interview_type.lower() == "coverletter-based interview":
            question_prompt = f"""
                You are a professional job interviewer with following personality: {persona} 

                Based on the given information, please generate specific and relevant interview questions that you might ask in a coverletter-based interview at an IT company. 

                Please keep your questions to one sentence, direct and clear.

                The question should especially be closely related to the "Coverletter". 

                IMPORTANT. NEVER ASK QUESTION ASKING WHAT THE USER DID OR EXPERIENCED IN THE {company_info}". The user never worked in {company_info}.
                IMPORTANT. The question should be MAINLY BASED ON THE EXPERIENCE WRITTEN IN THE "Coverletter"

                Information:
                Candidate profile: {user_profile}
                Target Company: {company_info}
                job of interest: {job_interest} 
                Coverletter: {coverletter}
            """
        else:
            raise ValueError("면접 유형은 '기술면접', '인성면접', '자기소개서 기반 면접' 중에서 선택해야 합니다.")

        if interview_atmosphere.lower() == "pressure interview" and context:
            question_prompt += f"""
                Consider the previously created interview questions and user's answers to that questions.
                Your question must be based on them, probing for additional clarification or pointing out contradictions in the user's previous answers.

                IMPORTANT. NEVER ASK QUESTION ASKING WHAT THE USER DID OR EXPERIENCED IN THE {company_info}". The user never worked in {company_info}.

                Previous questions and answers: {context}
            """

        question = question_agent.run(question_prompt)

        while question in generated_questions:
            question = question_agent.run(question_prompt)

        generated_questions.append(question)

        translated_question = translate(question, "en_to_ko")
        provide_ai_response(f"질문 {i + 1}: {translated_question}")

        answer = get_user_input("답변해 주세요: ", speech=False)
        translated_answer = translate(answer, "ko_to_en")

        if interview_atmosphere.lower() == "pressure interview":
            context += f"Question {i + 1}: {question}\nAnswer {i + 1}: {translated_answer}\n"

        evaluation_prompt = f"""
            You're a sharp, thorough, and critical job interviewer. You find out all the inconsistencies and parts that need further clarification in the interviewee's answers.
            As a professional job interviewer, evaluate the user answer to the interview question.
            When evaluating, consider both the overall quality of the answer and its relevance to the question.
            It is important to give a non-biased and objective comment for the user, giving helpful solutions to improve user's interview skill. 

            Question: {question}
            Answer: {translated_answer}
        """

        evaluation = feedback_agent.run(evaluation_prompt)
        translated_evaluation = translate(evaluation, "en_to_ko")
        # print(translated_evaluation)

        review.append(f"질문 {i + 1}에 대한 평가: {translated_evaluation}")

        if i < num_questions - 1:
            provide_ai_response("답변 감사합니다. 다음 질문으로 넘어가겠습니다.")

    provide_ai_response("면접 시뮬레이션이 끝났습니다. 다음은 각 답변에 대한 평가입니다:")
    for eval_result in review:
        provide_ai_response(eval_result)

    provide_ai_response("면접 준비에 많은 도움이 되셨기를 바랍니다!")


if __name__ == "__main__":
    interview_simulation()