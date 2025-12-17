import streamlit as st
import google.generativeai as genai
import os
import csv
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(page_title="수강생 전용 24시간 톡", page_icon="🎓")

# --- [경로 설정] ---
current_dir = os.path.dirname(os.path.abspath(__file__))
students_file_path = os.path.join(current_dir, "students.txt")
data_folder_path = os.path.join(current_dir, "data")
log_file_path = os.path.join(current_dir, "chat_logs.csv")

# --- [기능 1: 대화 내용 CSV 저장] ---
def save_log(user_email, question, answer):
    kst_now = datetime.utcnow() + timedelta(hours=9)
    timestamp = kst_now.strftime("%Y-%m-%d %H:%M:%S")
    
    file_exists = os.path.exists(log_file_path)
    
    with open(log_file_path, "a", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["시간", "사용자 이메일", "질문 내용", "AI 답변"])
        writer.writerow([timestamp, user_email, question, answer])

# --- [기능 2: 과거 대화 내용 불러오기 (새로 추가됨!)] ---
def load_chat_history(user_email):
    history = []
    if not os.path.exists(log_file_path):
        return history
    
    try:
        with open(log_file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 내 이메일로 된 기록만 가져오기
                if row.get("사용자 이메일") == user_email:
                    # 질문 넣기
                    history.append({"role": "user", "content": row.get("질문 내용")})
                    # 답변 넣기
                    history.append({"role": "assistant", "content": row.get("AI 답변")})
    except:
        pass
    return history

# --- [이메일 로그인 기능] ---
def check_login():
    user_email = st.session_state["email_input"].strip()
    try:
        with open(students_file_path, "r", encoding="utf-8") as f:
            allowed_users = [line.strip() for line in f.readlines()]
            
        if user_email in allowed_users:
            st.session_state["logged_in"] = True
            st.session_state["user_email"] = user_email
            # 🔥 로그인 성공 시 과거 기록 불러오기
            st.session_state.messages = load_chat_history(user_email)
            st.success(f"환영합니다! {user_email}님.")
        else:
            st.error("등록되지 않은 수강생 이메일입니다.")
    except FileNotFoundError:
        st.error("오류: 수강생 명단 파일을 찾을 수 없습니다.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("## 🎓 수강생 전용 로그인")
    st.write("강의 등록시 사용한 이메일을 입력해주세요.")
    st.text_input("이메일 주소", key="email_input", on_change=check_login)
    if st.button("로그인"):
        check_login()
    st.stop()

# --- [사이드바: 내 기록 다운로드] ---
with st.sidebar:
    st.header(f"{st.session_state['user_email']}님")
    
    # 내 대화 기록만 따로 필터링해서 다운로드 만들기
    if os.path.exists(log_file_path):
        my_logs = []
        with open(log_file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) > 1 and row[1] == st.session_state['user_email']:
                    my_logs.append(row)
        
        if my_logs:
            # 임시 파일 만들기
            my_csv_content = "시간,사용자 이메일,질문 내용,AI 답변\n"
            for log in my_logs:
                # CSV 형식을 지키기 위해 따옴표 처리 등을 포함한 간단 변환
                my_csv_content += ",".join([f'"{x}"' for x in log]) + "\n"

            st.download_button(
                label="💾 내 대화 기록 저장하기",
                data=my_csv_content.encode('utf-8-sig'),
                file_name=f"chat_history_{st.session_state['user_email']}.csv",
                mime="text/csv"
            )
        else:
            st.write("아직 대화 기록이 없습니다.")
            
    if st.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.session_state.messages = []
        st.rerun()

# --- [메인 채팅 기능] ---
st.title(f"🎓 유튜브 컨설팅 봇")
st.caption("이전 대화 내용이 자동으로 연결됩니다.")

# API 키 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("API 키 설정 오류")
    st.stop()

# 강의 자료 로딩
@st.cache_resource
def load_knowledge_base():
    knowledge_text = ""
    if not os.path.exists(data_folder_path):
        return ""
    files = [f for f in os.listdir(data_folder_path) if f.endswith('.txt')]
    for file in files:
        with open(os.path.join(data_folder_path, file), "r", encoding="utf-8") as f:
            knowledge_text += f"\n\n--- {file} ---\n\n" + f.read()
    return knowledge_text

knowledge_base = load_knowledge_base()

system_instruction = f"""
당신은 유튜브 채널 성장, 알고리즘, 기획, 수익화 등 모든 분야를 통달한 **'15년 차 최고의 유튜브 컨설턴트'**입니다.
**[당신의 행동 지침]**
1. 질문에 대한 답이 [강의 자료]에 있다면, 그 내용을 핵심 근거로 사용하여 답변하세요.
2. [강의 자료]에 없더라도, 절대 "자료에 없다"고 말하지 말고 당신의 전문 지식으로 완벽하게 답변하세요.
3. 수강생을 격려하는 따뜻한 멘토의 말투("~입니다", "~하셔야 해요")를 사용하세요.

**[강의 자료]**
{knowledge_base}
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction=system_instruction
)

# 화면에 대화 그리기
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 질문 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("답변 작성 중..."):
            try:
                # 최근 대화 몇 개만 추려서 보내기 (너무 길어지면 오류 날 수 있음)
                recent_history = []
                for m in st.session_state.messages[-10:]: # 최근 10개 대화만 기억
                     role = "model" if m["role"] == "assistant" else "user"
                     recent_history.append({"role": role, "parts": [m["content"]]})

                chat = model.start_chat(history=recent_history[:-1])
                response = chat.send_message(prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # 대화 저장
                save_log(st.session_state["user_email"], prompt, response.text)
                
            except Exception as e:
                st.error(f"오류: {e}")