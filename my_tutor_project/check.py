import streamlit as st
import google.generativeai as genai

st.title("🏥 API 긴급 진단")

# 1. API 키 확인
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.success(f"API 키를 찾았습니다! (앞 5자리: {api_key[:5]}...)")
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("API 키를 secrets.toml에서 불러오지 못했습니다.")
    st.stop()

# 2. 모델 목록 조회
st.subheader("내 키로 사용 가능한 모델 명단:")
try:
    model_list = []
    # 구글 서버에 직접 물어보는 명령어
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            model_list.append(m.name)
    
    if model_list:
        st.write(model_list)
        st.info("위 목록에 있는 이름 중 하나를 골라 app.py에 적어야 합니다.")
    else:
        st.warning("목록이 비어있습니다. API 키 권한을 확인해야 합니다.")
        
except Exception as e:
    st.error(f"모델 목록을 가져오는데 실패했습니다: {e}")
    st.write("힌트: API 키가 잘못되었거나, 구글 클라우드(Vertex AI) 키일 수 있습니다.")