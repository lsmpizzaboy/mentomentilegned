import streamlit as st
from supabase import create_client

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

st.set_page_config(page_title="멘토-멘티 시스템", page_icon="🏫")

# 2. 로그인 상태를 기억하는 저장소(Session State) 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student_id = None
    st.session_state.name = None

def logout():
    st.session_state.logged_in = False
    st.session_state.student_id = None
    st.session_state.name = None
    st.rerun()

# ==========================================
# 3. 로그인 및 회원가입 화면 (로그인 안 했을 때)
# ==========================================
if not st.session_state.logged_in:
    st.title("🏫 교내 멘토-멘티 시스템")
    
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    # --- 로그인 탭 ---
    with tab1:
        st.subheader("로그인")
        login_id = st.text_input("학번 (예: 10101)", key="login_id")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")
        
        if st.button("로그인하기"):
            if login_id and login_pw:
                # 데이터베이스에서 학번 검사
                res = supabase.table("students").select("*").eq("student_id", login_id).execute()
                
                if len(res.data) > 0 and res.data[0]["password"] == login_pw:
                    st.session_state.logged_in = True
                    st.session_state.student_id = login_id
                    st.session_state.name = res.data[0]["name"]
                    st.success(f"환영합니다, {res.data[0]['name']}님!")
                    st.rerun()
                else:
                    st.error("학번이나 비밀번호가 일치하지 않습니다.")
            else:
                st.warning("학번과 비밀번호를 모두 입력해 주세요.")
                
    # --- 회원가입 탭 ---
    with tab2:
        st.subheader("신규 회원가입")
        new_id = st.text_input("학번 (예: 10101)", key="new_id")
        new_name = st.text_input("이름 (실명)", key="new_name")
        new_pw = st.text_input("사용할 비밀번호", type="password", key="new_pw")
        
        if st.button("가입하기"):
            if new_id and new_name and new_pw:
                # 이미 가입된 학번인지 중복 검사
                check = supabase.table("students").select("*").eq("student_id", new_id).execute()
                if len(check.data) > 0:
                    st.error("이미 가입된 학번입니다! 로그인을 시도해 주세요.")
                else:
                    # 새 학생 정보 데이터베이스에 저장
                    new_student_data = {
                        "student_id": new_id,
                        "name": new_name,
                        "password": new_pw
                    }
                    supabase.table("students").insert(new_student_data).execute()
                    st.success("🎉 회원가입이 완료되었습니다! '로그인' 탭에서 로그인해 주세요.")
            else:
                st.warning("모든 칸을 빠짐없이 입력해 주세요.")

# ==========================================
# 4. 메인 화면 (로그인 성공 시 보이는 화면)
# ==========================================
else:
    # 사이드바에 내 정보 및 로그아웃 버튼 표시
    st.sidebar.write(f"👤 **{st.session_state.name}** ({st.session_state.student_id})")
    if st.sidebar.button("로그아웃"):
        logout()

    # --- 여기서부터 어제 만든 프로필 등록 코드가 시작됩니다 ---
    st.title("📝 멘토-멘티 프로필 등록")
    st.info("이곳에 어제 완성했던 프로필 등록 폼 코드가 들어갑니다!")
    
    # TODO: 어제 만든 st.form("profile_form") 코드를 이 아래에 그대로 붙여넣으시면 됩니다.
    # 데이터를 저장할 때, st.session_state.student_id 를 함께 저장하면 
    # "이 프로필을 작성한 사람이 누구인지" 완벽하게 기록할 수 있습니다!
