import streamlit as st
import google.generativeai as genai
import os
import csv
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(page_title="수강생 전용 24시간 톡", page_icon="🎓")

# --- [설정] ---
current_dir = os.path.dirname(os.path.abspath(__file__))
data_folder_path = os.path.join(current_dir, "data")
log_file_path = os.path.join(current_dir, "chat_logs.csv")

# --- [기능: 대화 내용 저장] ---
# 로그인은 없지만, '익명_게스트'라는 이름으로 질문 내용은 계속 기록됩니다.
def save_log(user_id, question, answer):
    kst_now = datetime.utcnow() + timedelta(hours=9)
    timestamp = kst_now.strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(log_file_path)
    with open(log_file_path, "a", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["시간", "사용자", "질문 내용", "AI 답변"])
        writer.writerow([timestamp, user_id, question, answer])

# --- [메인 화면] ---
st.title("🎓 유튜브 컨설팅 봇 (임시 오픈)")
st.caption("로그인 없이 자유롭게 이용 가능한 임시 버전입니다.")

# 사용자 ID를 '익명'으로 고정
if "user_id" not in st.session_state:
    st.session_state["user_id"] = "익명_게스트"

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

# 화면 그리기
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
                recent_history = []
                for m in st.session_state.messages[-10:]:
                     role = "model" if m["role"] == "assistant" else "user"
                     recent_history.append({"role": role, "parts": [m["content"]]})

                chat = model.start_chat(history=recent_history[:-1])
                response = chat.send_message(prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # 익명으로 대화 내용 저장
                save_log(st.session_state["user_id"], prompt, response.text)
                
            except Exception as e:
                st.error(f"오류: {e}")