import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();

  const logout = async () => {
    await apiFetch('/api/members/logout/', { method: 'POST' });
    setUser(null);
    navigate('/');
  };

  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div className="container">
          <Link className="navbar-brand fw-bold" to="/">AI 통합 서비스</Link>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav"><span className="navbar-toggler-icon" /></button>
          <div className="collapse navbar-collapse" id="mainNav">
            <div className="navbar-nav me-auto">
              <NavLink className="nav-link" to="/boards">게시판</NavLink>
              {user && <NavLink className="nav-link" to="/rag">RAG 검색</NavLink>}
              {user && <NavLink className="nav-link" to="/ai">멀티모달 AI</NavLink>}
              {user?.is_staff || user?.is_superuser ? <NavLink className="nav-link" to="/admin/members">회원관리</NavLink> : null}
            </div>
            <div className="d-flex align-items-center gap-2">
              {user ? <>
                <Link className="text-light text-decoration-none" to="/profile">{user.display_name}님</Link>
                <button className="btn btn-outline-light btn-sm" onClick={logout}>로그아웃</button>
              </> : <>
                <Link className="btn btn-outline-light btn-sm" to="/login">로그인</Link>
                <Link className="btn btn-primary btn-sm" to="/signup">회원가입</Link>
              </>}
            </div>
          </div>
        </div>
      </nav>
      <main className="container py-4"><Outlet /></main>
    </>
  );
}
