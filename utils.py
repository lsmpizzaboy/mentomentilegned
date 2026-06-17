import streamlit as st

@st.cache_data(ttl=60)
def get_cached_profiles(_supabase):
    try:
        res = _supabase.table("profiles").select("*").execute()
        return res.data
    except Exception:
        return []

# 💡 [핵심 최적화] 알림 데이터를 딱 10초 동안만 기억하게 만듭니다!
@st.cache_data(ttl=10)
def get_cached_notifications(_supabase, student_id):
    try:
        mentor_req = _supabase.table("matches").select("id, mentee_id").eq("mentor_id", student_id).eq("status", "대기중").execute()
        pending_matches = mentor_req.data
        
        res1 = _supabase.table("matches").select("id").eq("mentor_id", student_id).execute()
        res2 = _supabase.table("matches").select("id").eq("mentee_id", student_id).execute()
        my_match_ids = [m["id"] for m in res1.data] + [m["id"] for m in res2.data]
        
        unread_chats = []
        if my_match_ids:
            chat_res = _supabase.table("chat_messages").select("*").in_("match_id", my_match_ids).eq("is_read", False).neq("sender_id", student_id).execute()
            unread_chats = chat_res.data
            
        my_posts_res = _supabase.table("qna_board").select("id, title").eq("author_id", student_id).execute()
        my_post_ids = [p["id"] for p in my_posts_res.data]
        
        recent_comments = []
        if my_post_ids:
            comments_res = _supabase.table("qna_comments").select("*").in_("post_id", my_post_ids).eq("is_read", False).order("created_at", desc=True).execute()
            recent_comments = comments_res.data
            
        return pending_matches, unread_chats, recent_comments, my_match_ids, my_post_ids
    except:
        return [], [], [], [], []

def render_global_notification_center(supabase):
    st.sidebar.markdown("---") 
    
    student_id = st.session_state.student_id
    
    # 💡 10초 캐시 함수 호출 (이제 DB에 매번 안 물어보고 0.001초 만에 가져옵니다!)
    pending_matches, unread_chats, recent_comments, my_match_ids, my_post_ids = get_cached_notifications(supabase, student_id)

    total_notifications = len(pending_matches) + len(unread_chats) + len(recent_comments)
    badge = f" 🔴 ({total_notifications})" if total_notifications > 0 else ""
    
    with st.sidebar.popover(f"🔔 실시간 알림 센터{badge}", use_container_width=True):
        st.markdown("### 🗂️ 새로운 소식")
        
        if total_notifications == 0:
            st.caption("새로운 알림이 없습니다. 아주 평화롭네요! ✨")
        else:
            if st.button("🧹 새 알림 모두 확인(지우기)", use_container_width=True):
                if my_post_ids:
                    supabase.table("qna_comments").update({"is_read": True}).in_("post_id", my_post_ids).eq("is_read", False).execute()
                if my_match_ids:
                    supabase.table("chat_messages").update({"is_read": True}).in_("match_id", my_match_ids).neq("sender_id", student_id).eq("is_read", False).execute()
                
                # 지운 후에는 캐시(기억)도 초기화해서 바로 반영되게 만듭니다!
                get_cached_notifications.clear()
                st.rerun()

        if pending_matches:
            st.markdown("**🤝 멘토링 요청**")
            for m in pending_matches:
                st.info(f"🙋‍♂️ `{m['mentee_id']}` 학생이 멘토링 신청을 보냈습니다!")
            st.caption("※ 매칭 요청은 [매칭 시스템]에서 수락/거절해야 지워집니다.")
        
        if unread_chats:
            st.markdown("**💬 안 읽은 메시지**")
            unique_match_ids = set([c["match_id"] for c in unread_chats])
            st.warning(f"현재 답변을 기다리는 대화방이 {len(unique_match_ids)}개 있습니다.")
            
        if recent_comments:
            st.markdown("**💡 내 질문에 달린 새 댓글**")
            try:
                profile_res = supabase.table("qna_board").select("id, title").execute()
                post_title_dict = {p["id"]: p["title"] for p in profile_res.data}
                for c in recent_comments:
                    p_title = post_title_dict.get(c["post_id"], "내 질문")
                    st.caption(f"📌 '{p_title}' 글")
                    st.write(f"👉 {c['comment']}")
            except:
                st.caption("댓글을 불러왔습니다.")
                # ==========================================
# 💡 페이지 이동 감지 및 세션(채팅/게시글) 자동 초기화 센서
# ==========================================
def manage_page_state(current_page_name):
    # 처음 접속했을 때 현재 페이지 이름 저장
    if "last_page" not in st.session_state:
        st.session_state.last_page = current_page_name
        
    # 만약 '이전에 있던 페이지'와 '지금 들어온 페이지'가 다르다면? (메뉴를 이동했다면!)
    if st.session_state.last_page != current_page_name:
        # 켜져 있던 채팅방이나 상세 게시글 상태를 강제로 삭제해서 목록으로 되돌림
        if "current_chat_match" in st.session_state:
            del st.session_state.current_chat_match
        if "current_post" in st.session_state:
            del st.session_state.current_post
            
        # 다시 현재 페이지로 업데이트
        st.session_state.last_page = current_page_name
