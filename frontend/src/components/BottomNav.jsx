import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Camera, Star, Gift } from 'lucide-react';

const BottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'Home', icon: Camera },
    { path: '/rate', label: 'Rate', icon: Star },
    { path: '/pricing', label: 'Pricing', icon: Gift },
  ];

  return (
    <div className="bottom-nav lg:hidden">
      {navItems.map(item => (
        <button
          key={item.path}
          onClick={() => navigate(item.path)}
          className={`flex flex-col items-center gap-1 ${
            location.pathname === item.path ? 'text-[#1A1A1A]' : 'text-[#666666]'
          }`}
          data-testid={`nav-${item.label.toLowerCase()}`}
        >
          <item.icon size={24} strokeWidth={1.5} />
          <span className="text-xs">{item.label}</span>
        </button>
      ))}
    </div>
  );
};

export default BottomNav;
