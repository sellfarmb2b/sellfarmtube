import streamlit as st
import google.generativeai as genai
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="수강생 전용 24시간 톡", page_icon="🎓")

# --- [이메일 로그인 기능] ---
def check_login():
    user_email = st.session_state["email_input"].strip()
    try:
        with open("students.txt", "r", encoding="utf-8") as f:
            allowed_users = [line.strip() for line in f.readlines()]
            
        if user_email in allowed_users:
            st.session_state["logged_in"] = True
            st.session_state["user_email"] = user_email
            st.success(f"환영합니다! {user_email}님.")
        else:
            st.error("등록되지 않은 수강생 이메일입니다.")
    except FileNotFoundError:
        st.error("'students.txt' 파일이 없습니다. 관리자에게 문의하세요.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("## 🎓 수강생 전용 로그인")
    st.write("강의 등록시 사용한 이메일을 입력해주세요.")
    st.text_input("이메일 주소", key="email_input", on_change=check_login)
    if st.button("로그인"):
        check_login()
    st.stop()

# --- [채팅 기능 시작] ---

st.title(f"🎓 유튜브 컨설팅 봇 ({st.session_state['user_email']}님)")
st.caption("강의 내용 질문은 물론, 유튜브 관련 어떤 고민이든 물어보세요!")

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
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        return ""
    files = [f for f in os.listdir(data_folder) if f.endswith('.txt')]
    for file in files:
        with open(os.path.join(data_folder, file), "r", encoding="utf-8") as f:
            knowledge_text += f"\n\n--- {file} ---\n\n" + f.read()
    return knowledge_text

knowledge_base = load_knowledge_base()

# 페르소나 설정
system_instruction = f"""
당신은 유튜브 채널 성장, 알고리즘, 기획, 수익화 등 모든 분야를 통달한 **'15년 차 최고의 유튜브 컨설턴트'**입니다.
수강생들은 당신을 믿고 따르는 멘티들입니다.

**[당신의 행동 지침]**
1. **강의 자료 우선:** 질문에 대한 답이 아래 [강의 자료]에 있다면, 그 내용을 핵심 근거로 사용하여 답변하세요.
2. **제한 없는 답변:** 질문 내용이 [강의 자료]에 없더라도, 절대 "자료에 없다"고 말하지 마세요. 대신 **당신이 가진 방대한 유튜브 전문 지식을 총동원하여** 가장 완벽하고 구체적인 해결책을 제시하세요.
3. **전문가 톤:** 답변은 자신감 넘치고 전문적이어야 하며, 동시에 수강생을 격려하는 따뜻한 멘토의 말투("~입니다", "~하셔야 해요")를 사용하세요.
4. **디테일:** 추상적인 조언 대신, 당장 실행할 수 있는 구체적인 팁이나 예시를 포함하세요.

**[강의 자료]**
{knowledge_base}
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction=system_instruction
)

# 채팅 기록
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
        with st.spinner("전문가가 답변을 작성 중입니다..."):
            try:
                # 🔥 [수정된 부분] assistant를 model로 이름표 바꿔주기
                history_for_api = []
                for m in st.session_state.messages[:-1]:
                    # Streamlit의 'assistant'를 Gemini의 'model'로 변환
                    role = "model" if m["role"] == "assistant" else "user"
                    history_for_api.append({"role": role, "parts": [m["content"]]})
                
                chat = model.start_chat(history=history_for_api)
                response = chat.send_message(prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"오류: {e}")