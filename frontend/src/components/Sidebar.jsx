import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Camera, Star, Gift, LogOut, Settings } from 'lucide-react';
import { useAuth } from '../App';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', label: 'Home', icon: Camera },
    { path: '/rate', label: 'Rate Others', icon: Star },
    { path: '/pricing', label: 'Pricing', icon: Gift },
  ];

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="mb-8">
        <h1 
          className="text-2xl cursor-pointer"
          style={{ fontFamily: 'Georgia, serif' }}
          onClick={() => navigate('/dashboard')}
        >
          MatchMe
        </h1>
      </div>

      {/* User Info */}
      <div className="mb-6 p-4 bg-[#F7F7F5] rounded-[16px]">
        <p className="font-medium text-[#1A1A1A] truncate">{user?.name || 'User'}</p>
        <p className="text-sm text-[#666666] truncate">{user?.email}</p>
        <div className="mt-2 badge badge-lilac">
          <Star size={12} className="mr-1" fill="#1A1A1A" />
          {Math.floor(user?.credits || 0)} credits
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2">
        {navItems.map(item => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`sidebar-nav-item w-full ${location.pathname === item.path ? 'active' : ''}`}
            data-testid={`sidebar-${item.label.toLowerCase().replace(' ', '-')}`}
          >
            <item.icon size={20} strokeWidth={1.5} />
            {item.label}
          </button>
        ))}
      </nav>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="sidebar-nav-item w-full mt-auto text-[#666666] hover:text-[#E5533C]"
        data-testid="sidebar-logout"
      >
        <LogOut size={20} strokeWidth={1.5} />
        Log out
      </button>
    </aside>
  );
};

export default Sidebar;
