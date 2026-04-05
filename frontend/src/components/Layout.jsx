import React from 'react';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';
import { useAuth } from '../App';

const Layout = ({ children, showNav = true }) => {
  const { user } = useAuth();

  if (!showNav || !user) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-[#FFFFFD]">
      {/* Desktop Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <main className="lg:ml-[240px] min-h-screen">
        {children}
      </main>
      
      {/* Mobile Bottom Nav */}
      <BottomNav />
    </div>
  );
};

export default Layout;
