import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../App';

const formatApiErrorDetail = (detail) => {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
};

const Auth = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, user } = useAuth();
  
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already logged in
  React.useEffect(() => {
    if (user) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [user, navigate, location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        toast.success('Welcome back!');
      } else {
        await register(email, password, name);
        toast.success('Account created!');
      }
      navigate('/dashboard');
    } catch (err) {
      const errorMsg = formatApiErrorDetail(err.response?.data?.detail) || err.message;
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar">
        <button 
          onClick={() => navigate('/')}
          className="p-2 -ml-2"
          data-testid="back-btn"
        >
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          MatchMe
        </h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Toggle */}
          <div className="flex justify-center mb-8">
            <div className="toggle-group">
              <button
                className={`toggle-option ${isLogin ? 'active' : ''}`}
                onClick={() => setIsLogin(true)}
                data-testid="login-toggle"
              >
                Log in
              </button>
              <button
                className={`toggle-option ${!isLogin ? 'active' : ''}`}
                onClick={() => setIsLogin(false)}
                data-testid="signup-toggle"
              >
                Sign up
              </button>
            </div>
          </div>

          {/* Google Auth */}
          <button
            onClick={handleGoogleAuth}
            className="btn-pill btn-secondary w-full mb-6 gap-3"
            data-testid="google-auth-btn"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <div className="flex items-center gap-4 mb-6">
            <div className="flex-1 h-px bg-[#E5E5E5]" />
            <span className="text-sm text-[#666666]">or</span>
            <div className="flex-1 h-px bg-[#E5E5E5]" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div className="relative">
                <User size={20} className="absolute left-0 top-3 text-[#666666]" strokeWidth={1.5} />
                <input
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-minimal pl-8"
                  required={!isLogin}
                  data-testid="name-input"
                />
              </div>
            )}
            
            <div className="relative">
              <Mail size={20} className="absolute left-0 top-3 text-[#666666]" strokeWidth={1.5} />
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-minimal pl-8"
                required
                data-testid="email-input"
              />
            </div>

            <div className="relative">
              <Lock size={20} className="absolute left-0 top-3 text-[#666666]" strokeWidth={1.5} />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-minimal pl-8"
                required
                minLength={6}
                data-testid="password-input"
              />
            </div>

            {error && (
              <p className="text-error text-sm" data-testid="error-message">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-pill btn-primary w-full"
              data-testid="submit-btn"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                isLogin ? 'Log in' : 'Create account'
              )}
            </button>
          </form>

          <p className="text-center text-sm text-[#666666] mt-8">
            By continuing, you agree to our{' '}
            <button onClick={() => navigate('/terms')} className="underline">Terms</button>
            {' '}and{' '}
            <button onClick={() => navigate('/privacy')} className="underline">Privacy Policy</button>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default Auth;
