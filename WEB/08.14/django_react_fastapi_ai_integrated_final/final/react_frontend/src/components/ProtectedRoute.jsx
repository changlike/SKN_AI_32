import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ admin = false }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="text-center py-5">로그인 상태를 확인하고 있습니다...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (admin && !(user.is_staff || user.is_superuser)) return <Navigate to="/" replace />;
  return <Outlet />;
}
