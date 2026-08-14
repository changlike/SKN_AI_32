import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import MemberAdminPage from './pages/MemberAdminPage';
import BoardListPage from './pages/BoardListPage';
import BoardDetailPage from './pages/BoardDetailPage';
import BoardFormPage from './pages/BoardFormPage';
import RagPage from './pages/RagPage';
import MultimodalPage from './pages/MultimodalPage';

export default function App(){return <BrowserRouter><Routes><Route element={<Layout/>}><Route path="/" element={<HomePage/>}/><Route path="/login" element={<LoginPage/>}/><Route path="/signup" element={<SignupPage/>}/><Route path="/boards" element={<BoardListPage/>}/><Route path="/boards/:id" element={<BoardDetailPage/>}/><Route element={<ProtectedRoute/>}><Route path="/profile" element={<ProfilePage/>}/><Route path="/boards/create" element={<BoardFormPage/>}/><Route path="/boards/:id/edit" element={<BoardFormPage/>}/><Route path="/rag" element={<RagPage/>}/><Route path="/ai" element={<MultimodalPage/>}/></Route><Route element={<ProtectedRoute admin/>}><Route path="/admin/members" element={<MemberAdminPage/>}/></Route></Route></Routes></BrowserRouter>}
