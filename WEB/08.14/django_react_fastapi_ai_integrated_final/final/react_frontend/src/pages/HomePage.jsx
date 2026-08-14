import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../api/client';

export default function HomePage() {
  const [posts, setPosts] = useState([]);
  useEffect(() => { apiFetch('/api/home/').then((data) => setPosts(data.recent_posts)).catch(() => setPosts([])); }, []);
  return <>
    <section className="p-5 mb-4 bg-light rounded-3 border">
      <div className="container-fluid py-3">
        <h1 className="display-6 fw-bold">React + Django + FastAPI AI 통합 서비스</h1>
        <p className="fs-5 mb-0">화면은 React, 회원·게시판·권한·API는 Django, RAG·멀티모달 AI는 FastAPI가 담당합니다.</p>
      </div>
    </section>
    <div className="card shadow-sm">
      <div className="card-header fw-bold">최근 게시글</div>
      <div className="list-group list-group-flush">
        {posts.length ? posts.map((post) => <Link key={post.id} className="list-group-item list-group-item-action d-flex justify-content-between" to={`/boards/${post.id}`}><span>{post.title}</span><small>{post.author.display_name}</small></Link>) : <div className="list-group-item text-muted">등록된 게시글이 없습니다.</div>}
      </div>
    </div>
  </>;
}
