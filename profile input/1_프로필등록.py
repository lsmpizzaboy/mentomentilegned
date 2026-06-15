import streamlit as st
from supabase import create_client
import datetime

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

st.set_page_config(page_title="교내 멘토-멘티 시스템", page_icon="🏫")

# 2. 로그인 상태 관리용 세션 초기화
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
# 3. 로그인 및 회원가입 화면
# ==========================================
if not st.session_state.logged_in:
    st.title("🏫 교내 멘토-멘티 시스템")
    st.write("서비스를 이용하시려면 로그인이나 회원가입을 해주세요.")
    
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with tab1:
        st.subheader("로그인")
        login_id = st.text_input("학번 (예: 10101)", key="login_id")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")
        
        if st.button("로그인하기"):
            if login_id and login_pw:
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
                
    with tab2:
        st.subheader("신규 회원가입")
        new_id = st.text_input("학번 (예: 10101)", key="new_id")
        new_name = st.text_input("이름 (실명)", key="new_name")
        new_pw = st.text_input("사용할 비밀번호", type="password", key="new_pw")
        
        if st.button("가입하기"):
            if new_id and new_name and new_pw:
                check = supabase.table("students").select("*").eq("student_id", new_id).execute()
                if len(check.data) > 0:
                    st.error("이미 가입된 학번입니다! 로그인을 시도해 주세요.")
                else:
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
# 4. 메인 화면: 로그인 후 프로필 등록 창
# ==========================================
else:
    # 사이드바 프로필 영역 및 로그아웃
    st.sidebar.write(f"👤 **{st.session_state.name}** 학생")
    st.sidebar.write(f"🆔 학번: {st.session_state.student_id}")
    if st.sidebar.button("로그아웃"):
        logout()

    st.title("📝 멘토-멘티 프로필 등록")
    st.write(f"**{st.session_state.name}**님, 매칭 시스템에 등록할 프로필 정보를 입력해 주세요.")
    
    # 역할 선택 (멘토/멘티)
    role = st.radio("당신의 역할은 무엇인가요?", ("멘토", "멘티"))

    # 프로필 입력 폼 구성
    with st.form("profile_form"):
        # 이름은 로그인 정보를 바탕으로 자동 고정 (수정 불가로 안정성 확보)
        st.text_input("이름", value=st.session_state.name, disabled=True)
        
        subject_list = ["국어", "수학", "영어", "과탐", "사탐","수행평가", "기타"]
        time_list = ["평일 방과후", "평일 저녁", "주말 오전", "주말 오후", "주말 저녁"]
        
        date_range = []
        
        if role == "멘토":
            subjects = st.multiselect("자신 있게 가르칠 수 있는 과목을 선택해 주세요.", subject_list)
            bio = st.text_area("한줄 자기소개 (나의 멘토링 방식이나 장점은 무엇인가요?)")
        else:
            subjects = st.multiselect("도움받고 싶은 과목을 선택해 주세요.", subject_list)
            bio = st.text_area("질문하고 싶은 부분이나 현재 고민을 편하게 적어주세요!")
            
            # 멘티에게만 보여주는 추가 날짜 입력칸
            today = datetime.date.today()
            next_week = today + datetime.timedelta(days=7)
            st.write("---")
            st.subheader("📅 도움 요청 기한")
            date_range = st.date_input("도움이 필요한 기간을 선택해 주세요 (시작일과 종료일 클릭)", value=(today, next_week), min_value=today)
            st.write("---")
            
        available_times = st.multiselect("멘토링이 가능한 시간대를 모두 골라주세요.", time_list)
        submitted = st.form_submit_button("프로필 등록 완료하기")
        
        if submitted:
            # 입력 검증
            is_date_valid = True
            mentee_deadline = None
            
            if role == "멘티":
                if not isinstance(date_range, tuple) or len(date_range) < 2:
                    is_date_valid = False
                    st.warning("⚠️ 기간 선택을 완료해 주세요! (시작일과 종료일 모두 클릭)")
                else:
                    # 데이테베이스에 저장하기 쉽게 문자열 형태로 형식 변환
                    mentee_deadline = f"{date_range[0]} ~ {date_range[1]}"
            
            if not subjects or not available_times or not is_date_valid:
                st.warning("⚠️ 필수 항목(과목, 시간대)을 올바르게 입력해 주세요!")
            else:
                with st.spinner("프로필을 저장하는 중입니다..."):
                    try:
                        # 전송할 데이터 묶음 구성 (누구의 프로필인지 student_id 저장)
                        profile_data = {
                            "student_id": st.session_state.student_id,
                            "role": role,
                            "name": st.session_state.name,
                            "subjects": subjects,
                            "available_times": available_times,
                            "bio": bio,
                            "mentee_deadline": mentee_deadline  # 멘토일 때는 자동으로 NULL(빈값) 저장됨
                        }
                        
                       
                        # 전송할 데이터 묶음 구성
                        profile_data = {
                            "student_id": st.session_state.student_id,
                            "role": role,
                            "name": st.session_state.name,
                            "subjects": subjects,
                            "available_times": available_times,
                            "bio": bio,
                            "mentee_deadline": mentee_deadline
                        }
                        
                        # --- [여기가 핵심 추가 부분입니다!] ---
                        # 1. 현재 학번으로 등록된 프로필이 이미 있는지 데이터베이스 검색
                        check_exist = supabase.table("profiles").select("*").eq("student_id", st.session_state.student_id).execute()
                        
                        # 2. 만약 검색 결과가 1개라도 있다면 에러 메시지 띄우고 저장 중단
                        if len(check_exist.data) > 0:
                            st.error(f"⚠️ 이미 프로필을 등록하셨습니다! 하나의 계정당 하나의 프로필만 가질 수 있습니다.")
                        
                        # 3. 검색 결과가 없다면(처음 등록이라면) 정상적으로 저장
                        else:
                            supabase.table("profiles").insert(profile_data).execute()
                            st.success(f"🎉 {st.session_state.name}님의 프로필이 안전하게 데이터베이스에 저장되었습니다!")
                        # -----------------------------------
                        
                    except Exception as e:
                        st.error(f"데이터베이스 저장 실패: {e}")
