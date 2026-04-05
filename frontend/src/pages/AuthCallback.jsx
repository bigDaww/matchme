import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { toast } from 'sonner';

const AuthCallback = () => {
  const navigate = useNavigate();
  const { googleAuth, setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = window.location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (sessionIdMatch) {
        const sessionId = sessionIdMatch[1];
        try {
          const user = await googleAuth(sessionId);
          toast.success('Welcome to MatchMe!');
          
          // Clear hash and navigate
          window.history.replaceState(null, '', window.location.pathname);
          
          if (user.onboarding_completed) {
            navigate('/dashboard', { replace: true, state: { user } });
          } else {
            navigate('/onboarding', { replace: true, state: { user } });
          }
        } catch (error) {
          console.error('Auth callback error:', error);
          toast.error('Authentication failed. Please try again.');
          navigate('/auth', { replace: true });
        }
      } else {
        navigate('/auth', { replace: true });
      }
    };

    processAuth();
  }, [googleAuth, navigate, setUser]);

  return (
    <div className="app-container flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-[#1A1A1A] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-[#666666]">Signing you in...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
