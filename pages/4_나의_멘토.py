import streamlit as st
from supabase import create_client
import base64
# 💡 [최적화] 캐싱 함수 추가 불러오기
from utils import render_global_notification_center, get_cached_profiles
from utils import manage_page_state
manage_page_state("1_프로필")

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요합니다.")
    st.stop()



# ==========================================
# [채팅방 화면 모드]
# ==========================================
if "current_chat_match" in st.session_state:
    match = st.session_state.current_chat_match
    st.subheader(f"💬 {match['partner_name']} 멘토님과의 대화")
    
    if st.button("◀ 목록으로 돌아가기"):
        del st.session_state.current_chat_match
        st.rerun()
        
    supabase.table("chat_messages").update({"is_read": True}).eq("match_id", match['id']).neq("sender_id", st.session_state.student_id).execute()
    
    chat_res = supabase.table("chat_messages").select("*").eq("match_id", match['id']).order("created_at", desc=False).execute()
    messages = chat_res.data
    
    chat_box = st.container(height=400)
    with chat_box:
        if not messages:
            st.info("궁금한 점이나 첫 인사를 남겨보세요!")
        for msg in messages:
            is_me = (msg["sender_id"] == st.session_state.student_id)
            sender_label = f"🙋‍♀️ {st.session_state.name} (나)" if is_me else f"👨‍🏫 {match['partner_name']} 멘토"
            
            with st.chat_message("user" if is_me else "assistant", avatar="🐥" if is_me else "👨‍🏫"):
                st.write(f"**{sender_label}**")
                if msg["message"].startswith("DATA_IMAGE:"):
                    img_base64 = msg["message"].replace("DATA_IMAGE:", "")
                    st.image(f"data:image/png;base64,{img_base64}", width=350)
                else:
                    st.write(msg["message"])
                
    with st.expander("📸 사진 보내기"):
        uploaded_file = st.file_uploader("이미지 파일", type=["png", "jpg", "jpeg"], key="img_uploader")
        if uploaded_file:
            if st.button("🚀 사진 전송하기"):
                base64_str = base64.b64encode(uploaded_file.read()).decode("utf-8")
                supabase.table("chat_messages").insert({"match_id": match['id'], "sender_id": st.session_state.student_id, "message": f"DATA_IMAGE:{base64_str}"}).execute()
                st.rerun()

    prompt = st.chat_input("메시지를 입력하세요...")
    if prompt:
        supabase.table("chat_messages").insert({"match_id": match['id'], "sender_id": st.session_state.student_id, "message": prompt}).execute()
        st.rerun()
        
    st.stop()

# ==========================================
# [목록 화면 모드] 기본 화면
# ==========================================
st.title("👩‍🎓 나의 멘토 연락망")

try:
    # 💡 [최적화] DB 통신 제거하고 메모리 캐시 불러오기
    all_profiles = get_cached_profiles(supabase)
    
    # 1. 진행 중인 멘토링
    st.subheader("🟢 진행 중인 멘토링")
    my_mentors_res = supabase.table("matches").select("*").eq("mentee_id", st.session_state.student_id).eq("status", "수락됨").execute()
    my_mentors = my_mentors_res.data
    
    if not my_mentors:
        st.info("현재 진행 중인 멘토가 없습니다.")
    else:
        for match in my_mentors:
            m_id = match["mentor_id"]
            mentor_profile = next((p for p in all_profiles if p["student_id"] == m_id and p["role"] == "멘토"), {})
            mentor_name = mentor_profile.get("name", "알 수 없는 멘토")
            
            unread_res = supabase.table("chat_messages").select("id", count="exact").eq("match_id", match["id"]).eq("is_read", False).neq("sender_id", st.session_state.student_id).execute()
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    alert = f" 🔴 **새 메시지 {unread_res.count}건**" if unread_res.count > 0 else ""
                    st.write(f"**👨‍🏫 멘토:** {mentor_name} ({m_id}) {alert}")
                    with st.expander("🔍 이 멘토의 프로필 상세보기"):
                        st.write(f"📚 **자신 있는 과목:** {', '.join(mentor_profile.get('subjects', []))}")
                        st.write(f"⏰ **멘토링 시간대:** {', '.join(mentor_profile.get('available_times', []))}")
                        st.write(f"💬 **멘토 소개:** {mentor_profile.get('bio', '')}")
                with col2:
                    if st.button("💬 질문하러 가기", key=f"chat_{match['id']}", use_container_width=True):
                        st.session_state.current_chat_match = {"id": match["id"], "partner_name": mentor_name}
                        st.rerun()

    st.markdown("---")
    
    # 2. 종료된 멘토링 (별점 평가)
    st.subheader("⭐ 종료된 멘토링 리뷰 남기기")
    ended_res = supabase.table("matches").select("*").eq("mentee_id", st.session_state.student_id).eq("status", "종료됨").execute()
    needs_rating = [m for m in ended_res.data if m.get("rating") is None]
    
    if not needs_rating:
        st.info("평가를 기다리는 멘토링이 없습니다.")
    else:
        for match in needs_rating:
            m_id = match["mentor_id"]
            mentor_profile = next((p for p in all_profiles if p["student_id"] == m_id and p["role"] == "멘토"), {})
            mentor_name = mentor_profile.get("name", "알 수 없는 멘토")
            
            with st.container(border=True):
                st.write(f"**👨‍🏫 {mentor_name}** 멘토님과의 멘토링이 종료되었습니다. 어떠셨나요?")
                
                rating_options = {
                    "⭐⭐⭐⭐⭐ (5점 - 최고!)": 5,
                    "⭐⭐⭐⭐ (4점 - 좋아요)": 4,
                    "⭐⭐⭐ (3점 - 보통)": 3,
                    "⭐⭐ (2점 - 아쉬움)": 2,
                    "⭐ (1점 - 별로)": 1
                }
                selected_star = st.radio("별점을 선택해주세요:", list(rating_options.keys()), horizontal=True, key=f"star_{match['id']}")
                
                if st.button("🌟 별점 등록완료", key=f"rate_btn_{match['id']}"):
                    score = rating_options[selected_star]
                    supabase.table("matches").update({"rating": score}).eq("id", match["id"]).execute()
                    st.success(f"{mentor_name} 멘토님께 {score}점을 주셨습니다!")
                    st.rerun()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
