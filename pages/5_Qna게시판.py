import streamlit as st
from supabase import create_client
import base64
# 💡 [최적화] 캐싱 함수 함께 불러오기
from utils import render_global_notification_center, get_cached_profiles

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요한 서비스입니다.")
    st.stop()

render_global_notification_center(supabase)

# ==========================================
# 💡 [최적화] DB 호출 제거: 캐시 메모리에서 프로필 가져와 딕셔너리 빌드 (0.001초)
# ==========================================
all_profiles = get_cached_profiles(supabase)
profile_dict = {p["student_id"]: p["name"] for p in all_profiles}

# ==========================================
# 🔍 [상세 보기 화면 모드]
# ==========================================
if "current_post" in st.session_state:
    post = st.session_state.current_post
    author_name = profile_dict.get(post["author_id"], "알 수 없는 사용자")
    
    # 💡 [새로운 기능] 내가 쓴 글을 조회할 때, 아직 안 읽은 댓글이 있다면 모두 '읽음' 처리!
    if post["author_id"] == st.session_state.student_id:
        supabase.table("qna_comments").update({"is_read": True}).eq("post_id", post["id"]).eq("is_read", False).execute()

    col_btn1, col_btn2 = st.columns([4, 1])
    with col_btn1:
        if st.button("◀ 목록으로 돌아가기"):
            del st.session_state.current_post
            st.rerun()
    with col_btn2:
        if post["author_id"] == st.session_state.student_id:
            if st.button("🗑️ 글 삭제하기", type="primary", use_container_width=True):
                supabase.table("qna_board").delete().eq("id", post["id"]).execute()
                st.success("게시글이 성공적으로 삭제되었습니다.")
                del st.session_state.current_post
                st.rerun()
        
    st.title(f"📌 {post['title']}")
    st.caption(f"👤 작성자: {author_name} | 🕒 작성일: {post['created_at'][:10]}")
    st.markdown("---")
    
    st.write(post["content"])
    if post.get("image_data"):
        img_base64 = post["image_data"].replace("DATA_IMAGE:", "")
        st.image(f"data:image/png;base64,{img_base64}", width=400)
        
    st.markdown("---")
    st.subheader("💬 댓글")
    
    comments_res = supabase.table("qna_comments").select("*").eq("post_id", post["id"]).order("created_at", desc=False).execute()
    comments = comments_res.data
    
    if not comments:
        st.info("아직 댓글이 없습니다. 첫 번째 답변을 남겨주세요!")
    else:
        for c in comments:
            c_author_name = profile_dict.get(c["author_id"], "알 수 없는 사용자")
            st.markdown(f"- **{c_author_name}**: {c['comment']}")
            
            if c.get("image_data"):
                c_img_base64 = c["image_data"].replace("DATA_IMAGE:", "")
                st.image(f"data:image/png;base64,{c_img_base64}", width=250)
            
    st.write("") 
    
    with st.form(f"comment_form_{post['id']}", clear_on_submit=True):
        new_comment = st.text_input("새 댓글 남기기", placeholder="여기에 답변이나 의견을 입력하세요...")
        comment_image = st.file_uploader("사진 첨부 (선택사항)", type=["png", "jpg", "jpeg"], key=f"c_img_{post['id']}")
        submitted = st.form_submit_button("🚀 등록")
        
        if submitted:
            if new_comment or comment_image:
                c_image_base64 = None
                if comment_image:
                    c_image_base64 = base64.b64encode(comment_image.read()).decode("utf-8")
                    
                supabase.table("qna_comments").insert({
                    "post_id": post["id"],
                    "author_id": st.session_state.student_id,
                    "comment": new_comment if new_comment else "(사진을 첨부했습니다)",
                    "image_data": f"DATA_IMAGE:{c_image_base64}" if c_image_base64 else None
                }).execute()
                st.rerun() 
            else:
                st.warning("댓글 내용이나 사진을 입력해 주세요.")
                
    st.stop() 

# ==========================================
# 📋 [목록 화면 모드]
# ==========================================
st.title("💡 실시간 Q&A 질문게시판")
st.write("모르는 문제를 올리거나, 다른 친구들의 질문에 답변을 달아주세요!")

with st.expander("📝 새로운 질문 작성하기"):
    with st.form("new_post_form", clear_on_submit=True):
        new_title = st.text_input("제목 (어떤 과목/내용인지 간략히 적어주세요)")
        new_content = st.text_area("질문 내용", height=150)
        uploaded_image = st.file_uploader("사진 첨부 (선택사항)", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("🚀 질문 등록하기"):
            if new_title and new_content:
                image_base64 = None
                if uploaded_image:
                    image_base64 = base64.b64encode(uploaded_image.read()).decode("utf-8")
                
                post_data = {
                    "author_id": st.session_state.student_id,
                    "title": new_title,
                    "content": new_content,
                    "image_data": f"DATA_IMAGE:{image_base64}" if image_base64 else None
                }
                supabase.table("qna_board").insert(post_data).execute()
                st.success("질문이 등록되었습니다!")
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해 주세요.")

st.markdown("---")

search_query = st.text_input("🔍 질문 제목 검색", placeholder="찾고 싶은 질문의 제목을 입력해 보세요...")

st.subheader("📋 질문 목록")

try:
    posts_res = supabase.table("qna_board").select("*").order("created_at", desc=True).execute()
    posts = posts_res.data
    
    comments_res = supabase.table("qna_comments").select("post_id").execute()
    comment_counts = {}
    for c in comments_res.data:
        pid = c["post_id"]
        comment_counts[pid] = comment_counts.get(pid, 0) + 1
        
    if search_query:
        filtered_posts = [p for p in posts if search_query.lower() in p["title"].lower()]
    else:
        filtered_posts = posts
        
    if not filtered_posts:
        if search_query:
            st.info(f"'{search_query}'(으)로 검색된 질문이 없습니다.")
        else:
            st.info("아직 등록된 질문이 없습니다. 첫 번째 질문의 주인공이 되어보세요!")
    else:
        for post in filtered_posts:
            author_name = profile_dict.get(post["author_id"], "알 수 없는 사용자")
            ccount = comment_counts.get(post["id"], 0)
            
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{post['title']}**")
                    st.caption(f"👤 {author_name}  |  💬 댓글 {ccount}개")
                with col2:
                    if st.button("자세히 보기", key=f"view_{post['id']}", use_container_width=True):
                        st.session_state.current_post = post
                        st.rerun()

except Exception as e:
    st.error(f"게시판 데이터를 불러오는 중 오류가 발생했습니다: {e}")
