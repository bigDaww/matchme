import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Bell, Clock } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const Waiting = () => {
  const navigate = useNavigate();
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifyEnabled, setNotifyEnabled] = useState(false);

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
      }
    } catch (error) {
      console.error('Failed to fetch job');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="app-container flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#1A1A1A] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const isPriority = job?.priority === 'paid';

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          Processing
        </h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 rounded-full border-4 border-[#E5E5E5] border-t-[#C9B8E8] mb-8"
        />

        <h2 
          className="font-heading text-2xl mb-3"
          style={{ fontFamily: 'Georgia, serif' }}
        >
          {job?.type === 'best-shot' ? 'Finding your best shot' : 'Analyzing your profile'}
        </h2>

        <p className="text-[#666666] mb-6">
          Real people are reviewing your photos right now.
        </p>

        <div className="card w-full max-w-xs mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Clock size={20} className={isPriority ? 'text-[#C9B8E8]' : 'text-[#666666]'} />
            <span className="font-medium">
              {isPriority ? 'Priority queue' : 'Standard queue'}
            </span>
          </div>
          <p className="text-sm text-[#666666]">
            {isPriority 
              ? 'Results within 2 hours'
              : 'Results within 24 hours'}
          </p>
        </div>

        <button
          onClick={() => setNotifyEnabled(!notifyEnabled)}
          className={`btn-pill ${notifyEnabled ? 'btn-accent' : 'btn-secondary'} gap-2`}
          data-testid="notify-btn"
        >
          <Bell size={18} />
          {notifyEnabled ? 'Notifications on' : 'Notify me when ready'}
        </button>

        <p className="text-xs text-[#666666] mt-8">
          Job ID: {jobId?.slice(0, 8)}...
        </p>
      </div>
    </div>
  );
};

export default Waiting;
