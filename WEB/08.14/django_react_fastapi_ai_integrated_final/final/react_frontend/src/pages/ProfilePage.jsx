import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch, resolveDjangoUrl } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Alert from '../components/Alert';
import { formatFormErrors } from '../utils/errors';

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [values,setValues]=useState({display_name:'',email:'',gender:'N',age:'',phone:''}); const [photo,setPhoto]=useState(null); const [message,setMessage]=useState(''); const [error,setError]=useState(''); const navigate=useNavigate();
  useEffect(()=>{if(user)setValues({display_name:user.display_name||'',email:user.email||'',gender:user.gender||'N',age:user.age??'',phone:user.phone||''});},[user]);
  const submit=async(e)=>{e.preventDefault();setError('');const fd=new FormData();Object.entries(values).forEach(([k,v])=>fd.append(k,v));if(photo)fd.append('photo',photo);try{const data=await apiFetch('/api/members/profile/',{method:'POST',body:fd});setUser(data.user);setMessage(data.message);}catch(err){setError(formatFormErrors(err));}};
  const withdraw=async()=>{if(!window.confirm('회원 탈퇴 시 작성 게시글도 함께 삭제될 수 있습니다. 탈퇴하시겠습니까?'))return;await apiFetch('/api/members/withdraw/',{method:'POST'});setUser(null);navigate('/');};
  return <div className="row g-4"><div className="col-lg-4"><div className="card shadow-sm"><div className="card-body text-center">
    {user?.photo_url ? <img src={resolveDjangoUrl(user.photo_url)} className="profile-photo mb-3" alt="프로필"/>:<div className="profile-placeholder mb-3">👤</div>}
    <h4>{user?.display_name}</h4><div className="text-muted">{user?.username}</div><div className="mt-2"><span className="badge text-bg-secondary">{user?.admin_yn==='Y'?'관리자':'일반회원'}</span></div>
  </div></div></div><div className="col-lg-8"><div className="card shadow-sm"><div className="card-body"><h3 className="mb-3">회원 정보 수정</h3><Alert type="success">{message}</Alert><Alert type="danger">{error}</Alert><form onSubmit={submit}>
    <label className="form-label">이름</label><input className="form-control mb-3" value={values.display_name} onChange={(e)=>setValues({...values,display_name:e.target.value})} required/>
    <label className="form-label">이메일</label><input type="email" className="form-control mb-3" value={values.email} onChange={(e)=>setValues({...values,email:e.target.value})} required/>
    <div className="row"><div className="col-md-6"><label className="form-label">성별</label><select className="form-select mb-3" value={values.gender} onChange={(e)=>setValues({...values,gender:e.target.value})}><option value="M">남성</option><option value="F">여성</option><option value="N">선택 안 함</option></select></div><div className="col-md-6"><label className="form-label">나이</label><input type="number" className="form-control mb-3" value={values.age} onChange={(e)=>setValues({...values,age:e.target.value})}/></div></div>
    <label className="form-label">전화번호</label><input className="form-control mb-3" value={values.phone} onChange={(e)=>setValues({...values,phone:e.target.value})}/>
    <label className="form-label">프로필 사진</label><input type="file" accept="image/*" className="form-control mb-3" onChange={(e)=>setPhoto(e.target.files[0]||null)}/>
    <div className="d-flex justify-content-between"><button type="button" className="btn btn-outline-danger" onClick={withdraw}>회원 탈퇴</button><button className="btn btn-primary">정보 수정</button></div>
  </form></div></div></div></div>;
}
