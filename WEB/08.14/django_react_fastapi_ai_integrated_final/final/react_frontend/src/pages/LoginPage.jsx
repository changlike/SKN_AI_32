import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiFetch, toFormData } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Alert from '../components/Alert';
import { formatFormErrors } from '../utils/errors';

export default function LoginPage() {
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const submit = async (e) => {
    e.preventDefault(); setError('');
    try {
      const data = await apiFetch('/api/members/login/', { method: 'POST', body: toFormData(form) });
      setUser(data.user); navigate('/boards');
    } catch (err) { setError(formatFormErrors(err)); }
  };
  return <div className="row justify-content-center"><div className="col-md-6 col-lg-5"><div className="card shadow-sm"><div className="card-body p-4">
    <h2 className="mb-4">로그인</h2><Alert type="danger">{error}</Alert>
    <form onSubmit={submit}>
      <label className="form-label">회원 아이디</label><input className="form-control mb-3" value={form.username} onChange={(e)=>setForm({...form, username:e.target.value})} required />
      <label className="form-label">비밀번호</label><input type="password" className="form-control mb-3" value={form.password} onChange={(e)=>setForm({...form, password:e.target.value})} required />
      <button className="btn btn-primary w-100">로그인</button>
    </form><div className="mt-3 text-center"><Link to="/signup">회원가입</Link></div>
  </div></div></div></div>;
}
