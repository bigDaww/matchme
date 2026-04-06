import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Clock, Users } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import Layout from '../components/Layout';

const Waiting = () => {
  const navigate = useNavigate();
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJob();
    const interval = setInterval(fetchJob, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, [jobId]);

  const fetchJob = async () => {
    try {
      const response = await axios.get(`${API}/jobs/${jobId}`, { withCredentials: true });
      setJob(response.data);
      
      if (response.data.status === 'complete') {
        navigate(`/results/${jobId}`, { replace: true });
      } else if (response.data.status === 'failed') {
        // Stay on page but show failed state
      }
    } catch (error) {
      console.error('Failed to fetch job');
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

  if (job?.status === 'failed') {
    return (
      <Layout>
        <div className="min-h-screen">
          <div className="top-bar border-b border-[#E5E5E5]">
            <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2 lg:hidden" data-testid="back-btn">
              <ArrowLeft size={24} strokeWidth={1.5} />
            </button>
            <h1 className="text-xl lg:text-2xl" style={{ fontFamily: 'Georgia, serif' }}>
              Job Failed
            </h1>
            <div className="w-10 lg:hidden" />
          </div>

          <div className="flex-1 flex flex-col items-center justify-center px-6 py-16 md:py-24 text-center">
            <div className="w-20 h-20 rounded-full bg-[#E5533C] flex items-center justify-center mb-8">
              <span className="text-white text-3xl">!</span>
            </div>

            <h2 
              className="text-2xl md:text-3xl mb-4"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              We couldn't complete your review
            </h2>

            <p className="text-[#666666] mb-8 max-w-md">
              Unfortunately, we weren't able to gather enough reviews for your photos. 
              This can happen during periods of lower activity. Check your email for details.
            </p>

            <button
              onClick={() => navigate('/dashboard')}
              className="btn-pill btn-primary"
              data-testid="back-to-dashboard"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const tier = job?.tier || 'free';
  const tierInfo = {
    free: { time: '24 hours', reviewers: '3' },
    priority: { time: '2-4 hours', reviewers: '7' },
    pro: { time: '2-4 hours', reviewers: '10+' }
  }[tier];

  return (
    <Layout>
      <div className="min-h-screen">
        {/* Top Bar */}
        <div className="top-bar border-b border-[#E5E5E5]">
          <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2 lg:hidden" data-testid="back-btn">
            <ArrowLeft size={24} strokeWidth={1.5} />
          </button>
          <h1 className="text-xl lg:text-2xl" style={{ fontFamily: 'Georgia, serif' }}>
            Processing
          </h1>
          <div className="w-10 lg:hidden" />
        </div>

        <div className="flex-1 flex flex-col items-center justify-center px-6 py-16 md:py-24 text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-20 h-20 rounded-full border-4 border-[#E5E5E5] border-t-[#C9B8E8] mb-8"
          />

          <h2 
            className="text-2xl md:text-3xl mb-4"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            {job?.type === 'best-shot' ? 'Finding your best shot' : 'Analyzing your profile'}
          </h2>

          <p className="text-[#666666] mb-8 max-w-md">
            Real people are reviewing your photos right now. We'll email you when results are ready.
          </p>

          <div className="flex gap-4 mb-8">
            <div className="card text-center px-6 py-4">
              <Clock size={24} className="mx-auto mb-2 text-[#C9B8E8]" />
              <p className="text-sm text-[#666666]">Results in</p>
              <p className="font-medium">{tierInfo.time}</p>
            </div>
            <div className="card text-center px-6 py-4">
              <Users size={24} className="mx-auto mb-2 text-[#C9B8E8]" />
              <p className="text-sm text-[#666666]">Reviewed by</p>
              <p className="font-medium">{tierInfo.reviewers} people</p>
            </div>
          </div>

          {job?.extended && (
            <p className="text-sm text-[#666666] bg-[#F7F7F5] px-4 py-2 rounded-full mb-4">
              Extended review period active
            </p>
          )}

          <p className="text-xs text-[#666666]">
            Job ID: {jobId?.slice(0, 8)}...
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default Waiting;
