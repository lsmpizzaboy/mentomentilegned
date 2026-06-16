import streamlit as st
from supabase import create_client
import base64

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
        
    # 읽음 처리
    supabase.table("chat_messages").update({"is_read": True}).eq("match_id", match['id']).neq("sender_id", st.session_state.student_id).execute()
    
    chat_res = supabase.table("chat_messages").select("*").eq("match_id", match['id']).order("created_at", desc=False).execute()
    messages = chat_res.data
    
    chat_box = st.container(height=400)
    with chat_box:
        if not messages:
            st.info("궁금한 점이나 첫 인사를 남겨보세요!")
        for msg in messages:
            is_me = (msg["sender_id"] == st.session_state.student_id)
            
            # 💡 [기능 1] 로봇 대신 실제 보낸 사람의 이름을 말아주기
            sender_label = f"🙋‍♀️ {st.session_state.name} (나)" if is_me else f"👨‍🏫 {match['partner_name']} 멘토"
            
            with st.chat_message("user" if is_me else "assistant", avatar="🐥" if is_me else "👨‍🏫"):
                st.write(f"**{sender_label}**")
                
                # 💡 [기능 2] 이미지 메시지 처리
                if msg["message"].startswith("DATA_IMAGE:"):
                    img_base64 = msg["message"].replace("DATA_IMAGE:", "")
                    st.image(f"data:image/png;base64,{img_base64}", use_container_width=True)
                else:
                    st.write(msg["message"])
                
    # 💡 [기능 2] 사진 파일 업로더 추가
    with st.expander("📸 사진 보내기"):
        uploaded_file = st.file_uploader("이미지 파일을 선택하세요 (jpg, jpeg, png)", type=["png", "jpg", "jpeg"], key="img_uploader")
        if uploaded_file:
            if st.button("🚀 선택한 사진 전송하기"):
                file_bytes = uploaded_file.read()
                base64_str = base64.b64encode(file_bytes).decode("utf-8")
                supabase.table("chat_messages").insert({
                    "match_id": match['id'],
                    "sender_id": st.session_state.student_id,
                    "message": f"DATA_IMAGE:{base64_str}"
                }).execute()
                st.rerun()

    # 텍스트 입력창
    prompt = st.chat_input("메시지를 입력하세요...")
    if prompt:
        supabase.table("chat_messages").insert({
            "match_id": match['id'],
            "sender_id": st.session_state.student_id,
            "message": prompt
        }).execute()
        st.rerun()
        
    st.stop()

# ==========================================
# [목록 화면 모드] 기본 화면
# ==========================================
st.title("👩‍🎓 나의 멘토 연락망")

try:
    my_mentors_res = supabase.table("matches").select("*").eq("mentee_id", st.session_state.student_id).eq("status", "수락됨").execute()
    my_mentors = my_mentors_res.data
    
    profiles_res = supabase.table("profiles").select("*").execute()
    all_profiles = profiles_res.data  # 딕셔너리 대신 전체 리스트로 저장
    
    if not my_mentors:
        st.info("현재 매칭되어 진행 중인 멘토가 없습니다. '매칭 시스템'에서 멘토를 구해보세요!")
    else:
        for match in my_mentors:
            mentor_id = match["mentor_id"]
            # 💡 [핵심 수정] 학번이 일치하면서 동시에 역할이 '멘토'인 프로필만 정확하게 꼬집어옵니다!
            mentor_profile = next((p for p in all_profiles if p["student_id"] == mentor_id and p["role"] == "멘토"), {})
            mentor_name = mentor_profile.get("name", "알 수 없는 멘토")
            
            unread_res = supabase.table("chat_messages").select("id", count="exact").eq("match_id", match["id"]).eq("is_read", False).neq("sender_id", st.session_state.student_id).execute()
            unread_count = unread_res.count
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    alert = f" 🔴 **새 메시지 {unread_count}건**" if unread_count > 0 else ""
                    st.write(f"**👨‍🏫 멘토:** {mentor_name} ({mentor_id}) {alert}")
                    
                    # 💡 [기능 3] 관리창에서 상대방 프로필 즉시 보기
                    with st.expander("🔍 이 멘토의 프로필 상세보기"):
                        st.write(f"📚 **자신 있는 과목:** {', '.join(mentor_profile.get('subjects', []))}")
                        st.write(f"⏰ **멘토링 시간대:** {', '.join(mentor_profile.get('available_times', []))}")
                        st.write(f"💬 **멘토 소개:** {mentor_profile.get('bio', '')}")
                        
                with col2:
                    if st.button("💬 질문하러 가기", key=f"chat_{match['id']}", use_container_width=True):
                        st.session_state.current_chat_match = {"id": match["id"], "partner_name": mentor_name}
                        st.rerun()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
