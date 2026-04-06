import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Camera, Sparkles, Star, Gift, Clock, ChevronRight } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth, API } from '../App';
import Layout from '../components/Layout';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/user/dashboard`, { withCredentials: true });
      setDashboard(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-[#1A1A1A] border-t-transparent rounded-full animate-spin" />
        </div>
      </Layout>
    );
  }

  const credits = dashboard?.user?.credits ?? user?.credits ?? 0;
  const tier = dashboard?.user?.tier ?? user?.tier ?? 'free';

  return (
    <Layout>
      <div className="min-h-screen pb-nav">
        {/* Header */}
        <div className="px-6 md:px-8 lg:px-12 pt-6 md:pt-8 pb-4">
          <div className="max-w-[1200px] mx-auto lg:mx-0">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-sm text-[#666666]">Welcome back,</p>
                <h1 
                  className="text-2xl md:text-3xl"
                  style={{ fontFamily: 'Georgia, serif' }}
                >
                  {dashboard?.user?.name || user?.name || 'Friend'}
                </h1>
              </div>
              
              {/* Credits Badge - visible on mobile and tablet */}
              <div className="lg:hidden">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2"
                >
                  <div className="badge badge-lilac">
                    <Star size={14} className="mr-1" fill="#1A1A1A" />
                    {credits} credits
                  </div>
                </motion.div>
              </div>
            </div>

            {/* Desktop Credits & Tier */}
            <div className="hidden lg:flex items-center gap-3 mb-8">
              <div className="badge badge-lilac">
                <Star size={14} className="mr-1" fill="#1A1A1A" />
                {credits} credits
              </div>
              {tier !== 'free' && (
                <div className="badge badge-gray capitalize">{tier}</div>
              )}
            </div>
          </div>
        </div>

        <div className="px-6 md:px-8 lg:px-12 py-4">
          <div className="max-w-[1200px] mx-auto lg:mx-0">
            {/* Main Actions - responsive grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <button
                  onClick={() => navigate('/best-shot')}
                  className="card w-full text-left flex items-center gap-4 hover:shadow-lg transition-shadow"
                  data-testid="best-shot-btn"
                >
                  <div className="w-14 h-14 md:w-16 md:h-16 rounded-full bg-[#C9B8E8] flex items-center justify-center flex-shrink-0">
                    <Camera size={28} strokeWidth={1.5} className="text-[#1A1A1A]" />
                  </div>
                  <div className="flex-1">
                    <h3 
                      className="text-lg md:text-xl mb-1"
                      style={{ fontFamily: 'Georgia, serif' }}
                    >
                      Best Shot
                    </h3>
                    <p className="text-sm text-[#666666]">Find your best first photo</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-[#666666]">1 credit</span>
                    <ChevronRight size={20} className="text-[#E5E5E5]" />
                  </div>
                </button>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <button
                  onClick={() => navigate('/profile-analysis')}
                  className="card w-full text-left flex items-center gap-4 hover:shadow-lg transition-shadow"
                  data-testid="profile-analysis-btn"
                >
                  <div className="w-14 h-14 md:w-16 md:h-16 rounded-full bg-[#F7F7F5] flex items-center justify-center flex-shrink-0">
                    <Sparkles size={28} strokeWidth={1.5} className="text-[#1A1A1A]" />
                  </div>
                  <div className="flex-1">
                    <h3 
                      className="text-lg md:text-xl mb-1"
                      style={{ fontFamily: 'Georgia, serif' }}
                    >
                      Profile Analysis
                    </h3>
                    <p className="text-sm text-[#666666]">Get detailed profile feedback</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-[#666666]">2 credits</span>
                    <ChevronRight size={20} className="text-[#E5E5E5]" />
                  </div>
                </button>
              </motion.div>
            </div>

            {/* Two column layout for desktop */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Column */}
              <div>
                {/* Earn Credits */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="mb-8"
                >
                  <h2 className="text-sm text-[#666666] uppercase tracking-wider mb-3">
                    Earn free credits
                  </h2>
                  <button
                    onClick={() => navigate('/rate')}
                    className="card w-full text-left flex items-center gap-4 hover:shadow-lg transition-shadow"
                    data-testid="rate-others-btn"
                  >
                    <div className="w-14 h-14 rounded-full bg-[#F7F7F5] flex items-center justify-center flex-shrink-0">
                      <Gift size={28} strokeWidth={1.5} className="text-[#1A1A1A]" />
                    </div>
                    <div className="flex-1">
                      <h3 
                        className="text-lg mb-1"
                        style={{ fontFamily: 'Georgia, serif' }}
                      >
                        Rate Others
                      </h3>
                      <p className="text-sm text-[#666666]">
                        {dashboard?.stats?.ratings_today ?? 0} today • Rate 2 = 1 credit
                      </p>
                    </div>
                    <ChevronRight size={20} className="text-[#E5E5E5]" />
                  </button>
                </motion.div>

                {/* Upgrade CTA */}
                {tier === 'free' && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                  >
                    <button
                      onClick={() => navigate('/pricing')}
                      className="w-full py-5 px-6 rounded-[16px] bg-[#1A1A1A] text-white text-left hover:bg-[#333] transition-colors"
                      data-testid="upgrade-btn"
                    >
                      <p className="font-medium mb-1 text-lg">Get Priority Access</p>
                      <p className="text-sm opacity-80">Results in 2 hours instead of 24</p>
                    </button>
                  </motion.div>
                )}
              </div>

              {/* Right Column - Recent Results */}
              <div>
                {dashboard?.recent_jobs?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                  >
                    <h2 className="text-sm text-[#666666] uppercase tracking-wider mb-3">
                      Recent Results
                    </h2>
                    <div className="space-y-3">
                      {dashboard.recent_jobs.slice(0, 5).map((job) => (
                        <button
                          key={job.job_id}
                          onClick={() => {
                            if (job.status === 'complete') {
                              navigate(`/results/${job.job_id}`);
                            } else {
                              navigate(`/waiting/${job.job_id}`);
                            }
                          }}
                          className="card w-full text-left flex items-center gap-4 hover:shadow-lg transition-shadow"
                          data-testid={`job-${job.job_id}`}
                        >
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                            job.status === 'complete' ? 'bg-[#6B7E4A]' : 'bg-[#F7F7F5]'
                          }`}>
                            {job.status === 'complete' ? (
                              <Sparkles size={20} strokeWidth={1.5} className="text-white" />
                            ) : (
                              <Clock size={20} strokeWidth={1.5} className="text-[#666666]" />
                            )}
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium text-[#1A1A1A] capitalize">
                              {job.type.replace('-', ' ')}
                            </h3>
                            <p className="text-sm text-[#666666] capitalize">{job.status}</p>
                          </div>
                          <ChevronRight size={20} className="text-[#E5E5E5]" />
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
