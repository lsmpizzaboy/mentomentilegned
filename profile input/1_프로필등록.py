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
    
    tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with tab_login:
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
                
    with tab_signup:
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
# 4. 메인 화면: 내 프로필 통합 관리 창
# ==========================================
else:
    st.sidebar.write(f"👤 **{st.session_state.name}** 학생")
    st.sidebar.write(f"🆔 학번: {st.session_state.student_id}")
    if st.sidebar.button("로그아웃"):
        logout()

    st.title("📝 멘토-멘티 프로필 관리")
    st.write(f"**{st.session_state.name}**님, 나의 멘토 프로필과 멘티 프로필을 각각 관리할 수 있습니다.")
    
    try:
        profile_res = supabase.table("profiles").select("*").eq("student_id", st.session_state.student_id).execute()
        existing_profiles = profile_res.data
    except Exception as e:
        st.error(f"기존 프로필을 불러오는 중 오류 발생: {e}")
        existing_profiles = []
        
    mentor_profile = next((p for p in existing_profiles if p.get("role") == "멘토"), None)
    mentee_profile = next((p for p in existing_profiles if p.get("role") == "멘티"), None)
    
    st.markdown("### 📊 나의 프로필 현황")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if mentor_profile:
            st.success("👨‍🏫 멘토 프로필: **등록 완료** (수정 가능)")
        else:
            st.info("👨‍🏫 멘토 프로필: **미등록**")
    with col_m2:
        if mentee_profile:
            st.success("👩‍🎓 멘티 프로필: **등록 완료** (수정 가능)")
        else:
            st.info("👩‍🎓 멘티 프로필: **미등록**")
            
    st.markdown("---")
    
    subject_list = ["국어", "수학", "영어", "과학", "사회", "파이썬", "C언어", "기타"]
    time_list = ["평일 방과후", "평일 저녁", "주말 오전", "주말 오후", "주말 저녁"]
    
    # 💡 [핵심 변경] 라디오 버튼 대신 탭(Tabs)을 사용하여 화면을 완전히 분리!
    tab_mentor, tab_mentee = st.tabs(["👨‍🏫 멘토 프로필 관리", "👩‍🎓 멘티 프로필 관리"])
    
    # ----------------------------------------
    # [1] 👨‍🏫 멘토 프로필 탭
    # ----------------------------------------
    with tab_mentor:
        is_mentor_edit = mentor_profile is not None
        
        if is_mentor_edit:
            # 💡 [새로운 기능] 나의 평균 별점 계산 및 표시
            try:
                ratings_res = supabase.table("matches").select("rating").eq("mentor_id", st.session_state.student_id).not_.is_("rating", "null").execute()
                ratings = [r["rating"] for r in ratings_res.data if r["rating"] is not None]
                if ratings:
                    avg_score = sum(ratings) / len(ratings)
                    st.info(f"🏆 **나의 멘토 평균 별점:** {avg_score:.1f} / 5.0점 (총 {len(ratings)}명의 멘티가 평가함)")
                else:
                    st.info("⭐ 아직 받은 별점 평가가 없습니다. 첫 멘토링을 성공적으로 마쳐보세요!")
            except:
                pass
                
            st.caption("✨ 기존에 작성한 멘토 프로필 정보를 불러왔습니다. 수정 후 하단 버튼을 누르면 업데이트됩니다.")
        else:
            st.caption("✨ 아직 작성된 멘토 프로필이 없습니다. 새로 입력해 주세요.")

        m_default_subs = mentor_profile.get("subjects", []) if is_mentor_edit else []
        m_default_bio = mentor_profile.get("bio", "") if is_mentor_edit else ""
        m_default_times = mentor_profile.get("available_times", []) if is_mentor_edit else []

        with st.form("profile_form_멘토"):
            st.text_input("이름", value=st.session_state.name, disabled=True)
            m_valid_subs = [s for s in m_default_subs if s in subject_list]
            m_subjects = st.multiselect("자신 있게 가르칠 수 있는 과목을 선택해 주세요.", subject_list, default=m_valid_subs)
            m_bio = st.text_area("한줄 자기소개 (나의 멘토링 방식이나 장점은 무엇인가요?)", value=m_default_bio)
            m_valid_times = [t for t in m_default_times if t in time_list]
            m_times = st.multiselect("멘토링이 가능한 시간대를 모두 골라주세요.", time_list, default=m_valid_times)
            
            m_btn_text = "🔧 멘토 프로필 수정 완료하기" if is_mentor_edit else "🚀 멘토 프로필 신규 등록하기"
            m_submitted = st.form_submit_button(m_btn_text)
            
            if m_submitted:
                if not m_subjects or not m_times:
                    st.warning("⚠️ 필수 항목(과목, 시간대)을 올바르게 입력해 주세요!")
                else:
                    data = {"student_id": st.session_state.student_id, "role": "멘토", "name": st.session_state.name, "subjects": m_subjects, "available_times": m_times, "bio": m_bio}
                    if is_mentor_edit:
                        supabase.table("profiles").update(data).eq("student_id", st.session_state.student_id).eq("role", "멘토").execute()
                        st.success("🎉 멘토 프로필 수정이 완료되었습니다!")
                    else:
                        supabase.table("profiles").insert(data).execute()
                        st.success("🎉 멘토 프로필이 신규 등록되었습니다!")
                    st.rerun()
                    
        # 💡 [새로운 기능] 프로필 삭제 버튼 (폼 바깥에 위치)
        if is_mentor_edit:
            if st.button("🗑️ 내 멘토 프로필 목록에서 내리기 (삭제)", type="primary", use_container_width=True):
                supabase.table("profiles").delete().eq("student_id", st.session_state.student_id).eq("role", "멘토").execute()
                st.success("멘토 프로필이 삭제되었습니다. 이제 매칭 명단에 나타나지 않습니다.")
                st.rerun()

    # ----------------------------------------
    # [2] 👩‍🎓 멘티 프로필 탭
    # ----------------------------------------
    with tab_mentee:
        is_mentee_edit = mentee_profile is not None
        
        if is_mentee_edit:
            st.caption("✨ 기존에 작성한 멘티 프로필 정보를 불러왔습니다. 수정 후 하단 버튼을 누르면 업데이트됩니다.")
        else:
            st.caption("✨ 아직 작성된 멘티 프로필이 없습니다. 새로 입력해 주세요.")

        me_default_subs = mentee_profile.get("subjects", []) if is_mentee_edit else []
        me_default_bio = mentee_profile.get("bio", "") if is_mentee_edit else ""
        me_default_times = mentee_profile.get("available_times", []) if is_mentee_edit else []
        
        default_date = (datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7))
        if is_mentee_edit and mentee_profile.get("mentee_deadline"):
            try:
                dates = mentee_profile["mentee_deadline"].split(" ~ ")
                if len(dates) == 2:
                    default_date = (datetime.date.fromisoformat(dates[0]), datetime.date.fromisoformat(dates[1]))
            except: pass

        with st.form("profile_form_멘티"):
            st.text_input("이름", value=st.session_state.name, disabled=True)
            me_valid_subs = [s for s in me_default_subs if s in subject_list]
            me_subjects = st.multiselect("도움받고 싶은 과목을 선택해 주세요.", subject_list, default=me_valid_subs)
            me_bio = st.text_area("질문하고 싶은 부분이나 현재 고민을 편하게 적어주세요!", value=me_default_bio)
            
            st.write("---")
            st.subheader("📅 도움 요청 기한")
            # 💡 [달력 에러 해결 유지] min_value=today 를 지워서 과거 날짜여도 충돌 안 나게 처리!
            date_range = st.date_input("도움이 필요한 기간을 선택해 주세요 (시작일과 종료일 클릭)", value=default_date)
            st.write("---")
            
            me_valid_times = [t for t in me_default_times if t in time_list]
            me_times = st.multiselect("멘토링이 가능한 시간대를 모두 골라주세요.", time_list, default=me_valid_times)
            
            me_btn_text = "🔧 멘티 프로필 수정 완료하기" if is_mentee_edit else "🚀 멘티 프로필 신규 등록하기"
            me_submitted = st.form_submit_button(me_btn_text)
            
            if me_submitted:
                is_date_valid = True
                mentee_deadline = None
                if not isinstance(date_range, tuple) or len(date_range) < 2:
                    is_date_valid = False
                    st.warning("⚠️ 기간 선택을 완료해 주세요! (시작일과 종료일 모두 클릭)")
                else:
                    mentee_deadline = f"{date_range[0]} ~ {date_range[1]}"
                    
                if not me_subjects or not me_times or not is_date_valid:
                    st.warning("⚠️ 필수 항목(과목, 시간대, 기간)을 올바르게 입력해 주세요!")
                else:
                    data = {"student_id": st.session_state.student_id, "role": "멘티", "name": st.session_state.name, "subjects": me_subjects, "available_times": me_times, "bio": me_bio, "mentee_deadline": mentee_deadline}
                    if is_mentee_edit:
                        supabase.table("profiles").update(data).eq("student_id", st.session_state.student_id).eq("role", "멘티").execute()
                        st.success("🎉 멘티 프로필 수정이 완료되었습니다!")
                    else:
                        supabase.table("profiles").insert(data).execute()
                        st.success("🎉 멘티 프로필이 신규 등록되었습니다!")
                    st.rerun()

        # 💡 [새로운 기능] 프로필 삭제 버튼
        if is_mentee_edit:
            if st.button("🗑️ 내 멘티 프로필 목록에서 내리기 (삭제)", type="primary", use_container_width=True):
                supabase.table("profiles").delete().eq("student_id", st.session_state.student_id).eq("role", "멘티").execute()
                st.success("멘티 프로필이 삭제되었습니다.")
                st.rerun()
