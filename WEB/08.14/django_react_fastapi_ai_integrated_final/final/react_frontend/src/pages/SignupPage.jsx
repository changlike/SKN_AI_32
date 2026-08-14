import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Alert from '../components/Alert';
import { formatFormErrors } from '../utils/errors';

export default function SignupPage() {
  const [values, setValues] = useState({ username:'', display_name:'', email:'', gender:'N', age:'', phone:'', password1:'', password2:'' });
  const [photo, setPhoto] = useState(null); const [error,setError]=useState('');
  const { setUser } = useAuth(); const navigate=useNavigate();
  const change=(e)=>setValues({...values,[e.target.name]:e.target.value});
  const submit=async(e)=>{e.preventDefault();setError('');const fd=new FormData();Object.entries(values).forEach(([k,v])=>{if(v!=='')fd.append(k,v)});if(photo)fd.append('photo',photo);try{const data=await apiFetch('/api/members/signup/',{method:'POST',body:fd});setUser(data.user);navigate('/boards');}catch(err){setError(formatFormErrors(err));}};
  return <div className="row justify-content-center"><div className="col-lg-7"><div className="card shadow-sm"><div className="card-body p-4"><h2 className="mb-4">회원가입</h2><Alert type="danger">{error}</Alert><form onSubmit={submit} encType="multipart/form-data">
    <div className="row g-3">
      <div className="col-md-6"><label className="form-label">회원 아이디</label><input name="username" className="form-control" value={values.username} onChange={change} required /></div>
      <div className="col-md-6"><label className="form-label">이름</label><input name="display_name" className="form-control" value={values.display_name} onChange={change} required /></div>
      <div className="col-md-6"><label className="form-label">이메일</label><input name="email" type="email" className="form-control" value={values.email} onChange={change} required /></div>
      <div className="col-md-3"><label className="form-label">성별</label><select name="gender" className="form-select" value={values.gender} onChange={change}><option value="M">남성</option><option value="F">여성</option><option value="N">선택 안 함</option></select></div>
      <div className="col-md-3"><label className="form-label">나이</label><input name="age" type="number" min="0" className="form-control" value={values.age} onChange={change} /></div>
      <div className="col-md-6"><label className="form-label">전화번호</label><input name="phone" className="form-control" value={values.phone} onChange={change} /></div>
      <div className="col-md-6"><label className="form-label">프로필 사진</label><input type="file" accept="image/*" className="form-control" onChange={(e)=>setPhoto(e.target.files[0]||null)} /></div>
      <div className="col-md-6"><label className="form-label">비밀번호</label><input name="password1" type="password" className="form-control" value={values.password1} onChange={change} required /></div>
      <div className="col-md-6"><label className="form-label">비밀번호 확인</label><input name="password2" type="password" className="form-control" value={values.password2} onChange={change} required /></div>
    </div><button className="btn btn-primary mt-4 w-100">회원가입</button></form></div></div></div></div>;
}
