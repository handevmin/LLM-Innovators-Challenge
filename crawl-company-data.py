import os
import time
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# 환경변수 불러오기
load_dotenv()

# CATCH 아이디, 비밀번호 설정
catch_id = os.getenv("CATCH_ID")
catch_pwd = os.getenv("CATCH_PWD")

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# Chrome WebDriver 인스턴스 생성
driver = webdriver.Chrome(options=chrome_options)


# 폴더 생성 함수
def create_folder(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# 추출한 보고서를 markdown(.md) 파일로 저장하는 함수
def save_report_to_md(company_name, report_data, folder_path):
    # 파일 경로 생성
    file_name = f"{company_name}.md"
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, 'w', encoding='utf-8') as f:
        # 회사 이름을 헤더로 작성
        f.write(f"# {company_name} Report\n\n")

        # 추출한 섹션과 내용을 작성
        for section in report_data:
            f.write(f"## {section['title']}\n\n")  # 섹션 제목
            for content in section['content']:
                f.write(f"{content}\n\n")  # 섹션 내용

    print(f"Report saved: {file_path}")


# 중복 태그 추출을 피하면서 올바른 순서로 콘텐츠 추출 함수
def extract_content_from_section(section):
    content = []

    # 섹션 내의 각 태그를 순서대로 순회
    for element in section.find_all(True, recursive=False):
        if element.name == 'h1' or element.name == 'h2':
            content.append(f"### {element.get_text().strip()}")
        elif element.name == 'p':
            # 자식 요소가 없는 <p> 태그만 추가
            if not element.find(True, recursive=False):
                content.append(element.get_text().strip())
        elif element.name == 'ul':
            # 리스트 처리 <ul> -> <li>
            list_items = [f"- {li.get_text().strip()}" for li in element.find_all('li')]
            content.append('\n'.join(list_items))
        elif element.name == 'dl':
            # <dl> -> <dt>/<dd> 처리
            dts = element.find_all('dt')
            dds = element.find_all('dd')
            for dt, dd in zip(dts, dds):
                content.append(f"**{dt.get_text().strip()}**: {dd.get_text().strip()}")

    return content


# 단일 보고서 페이지에서 콘텐츠 추출 함수
def extract_report_content(driver):
    retries = 3
    wait = WebDriverWait(driver, 10)  # 명시적 대기 10초

    for attempt in range(retries):
        try:
            # 'h1' 요소(회사 이름)가 로드될 때까지 대기
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))

            # 페이지를 BeautifulSoup으로 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 회사 이름 찾기
            company_name_tag = soup.find('h1')
            if company_name_tag:
                company_name = company_name_tag.text.strip().replace(' ', '_')
            else:
                raise ValueError("회사 이름을 찾을 수 없음")

            # 보고서에서 섹션 추출
            sections = soup.find_all('div', class_='cont_wrap')
            report_data = []

            for section in sections:
                section_title_tag = section.find('h2')
                section_title = section_title_tag.text.strip() if section_title_tag else "Unnamed Section"

                # 섹션에서 단락, 리스트, dt/dd 내용 추출
                section_content = []
                for tag in section.find_all(['p', 'ul', 'dl']):
                    if tag.name == 'p':
                        section_content.append(tag.text.strip())
                    elif tag.name == 'ul':
                        list_items = [li.text.strip() for li in tag.find_all('li')]
                        section_content.append('\n'.join(list_items))
                    elif tag.name == 'dl':  # <dt>/<dd> 태그 처리
                        dts = tag.find_all('dt')
                        dds = tag.find_all('dd')
                        for dt, dd in zip(dts, dds):
                            section_content.append(f"**{dt.text.strip()}**: {dd.text.strip()}")

                # 실제 섹션 내용 추출, 중복 방지
                # section_content = extract_content_from_section(section)

                report_data.append({
                    'title': section_title,
                    'content': section_content
                })

            return company_name, report_data

        except Exception as e:
            print(f"{attempt + 1}번째 시도 실패: {e}")
            driver.implicitly_wait(2)  # 재시도 전 2초 대기
            if attempt == retries - 1:
                raise  # 재시도 횟수 초과 시 예외 발생


# 모든 보고서를 방문하고 markdown 파일로 저장하는 함수
def visit_reports_and_save_to_md(folder_path):
    # 폴더가 존재하는지 확인
    create_folder(folder_path)

    # 보고서 페이지 탐색
    while True:
        report_links = driver.find_elements(By.CSS_SELECTOR, 'ul.list li a.link')

        # 페이지의 보고서 링크 순회
        for i in range(len(report_links)):
            report_links[i].click()
            driver.implicitly_wait(2)

            # 새로운 탭으로 전환
            driver.switch_to.window(driver.window_handles[1])
            driver.implicitly_wait(3)

            # 보고서 내용 추출
            company_name, report_data = extract_report_content(driver)

            # 보고서를 markdown 파일로 저장
            save_report_to_md(company_name, report_data, folder_path)

            # 탭 닫고 메인 탭으로 전환
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        # 다음 페이지로 이동
        time.sleep(20)
        next_page_button = driver.find_element(By.CLASS_NAME, 'next')
        next_page_button.click()
        time.sleep(30)

    # 브라우저 종료
    driver.quit()


# 스크립트 실행 및 markdown 파일 저장 폴더 지정
folder_path = "company_reports_md"

# Google 홈페이지 열기
driver.get(url="https://www.catch.co.kr/Member/Login")
driver.implicitly_wait(2)

# 사용자 이름과 비밀번호 입력란 찾기 및 자격 증명 입력
username_input = driver.find_element(By.ID, 'id_login')
password_input = driver.find_element(By.ID, 'pw_login')

# 로그인 자격 증명 입력
username = catch_id
password = catch_pwd

# 로그인 정보 입력
username_input.send_keys(username)
password_input.send_keys(password)

# 로그인 버튼 찾기 및 클릭
login_button = driver.find_element(By.CLASS_NAME, 'mem_btn_join')
login_button.click()

# 로그인 완료 및 페이지 로드 대기
driver.implicitly_wait(2)

# 로그인 후 타겟 페이지로 이동
driver.get('https://www.catch.co.kr/Comp/AnalysisComp')

# 페이지 로드 후 약간의 시간 대기
driver.implicitly_wait(4)

visit_reports_and_save_to_md(folder_path)