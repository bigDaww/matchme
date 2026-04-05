import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Crown, Trash2, MessageSquare, Star } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const Results = () => {
  const navigate = useNavigate();
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [photos, setPhotos] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJob();
  }, [jobId]);

  const fetchJob = async () => {
    try {
      const response = await axios.get(`${API}/jobs/${jobId}`, { withCredentials: true });
      setJob(response.data);
      
      // Fetch photos
      const userPhotos = await axios.get(`${API}/user/photos`, { withCredentials: true });
      const photoMap = {};
      userPhotos.data.forEach(p => { photoMap[p.photo_id] = p; });
      setPhotos(photoMap);
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

  if (!job || job.status !== 'complete') {
    return (
      <div className="app-container">
        <div className="top-bar border-b border-[#E5E5E5]">
          <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2">
            <ArrowLeft size={24} strokeWidth={1.5} />
          </button>
          <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>Results</h1>
          <div className="w-10" />
        </div>
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="text-center">
            <p className="text-[#666666] mb-4">Results not ready yet.</p>
            <button onClick={() => navigate(`/waiting/${jobId}`)} className="btn-pill btn-primary">
              Check Status
            </button>
          </div>
        </div>
      </div>
    );
  }

  const result = job.result;
  const winner = result?.winner;
  const ranked = result?.ranked || [];

  return (
    <div className="app-container pb-nav">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          {job.type === 'best-shot' ? 'Your Best Shot' : 'Profile Analysis'}
        </h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 px-6 py-6 overflow-y-auto">
        {/* Winner */}
        {winner && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="relative">
              <img
                src={photos[winner.photo_id]?.preview || `${API}/files/${photos[winner.photo_id]?.storage_path}`}
                alt="Best photo"
                className="photo-tile mx-auto ring-4 ring-[#C9B8E8]"
                onError={(e) => { e.target.src = 'https://via.placeholder.com/300x400?text=Photo'; }}
                data-testid="winner-photo"
              />
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 badge badge-lilac gap-1">
                <Crown size={14} />
                Best First Photo
              </div>
            </div>

            {/* Stats */}
            <div className="flex justify-center gap-4 mt-6">
              <div className="text-center">
                <p className="text-2xl font-medium">{winner.avg_confident?.toFixed(1) || '-'}</p>
                <p className="text-xs text-[#666666]">Confident</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-medium">{winner.avg_approachable?.toFixed(1) || '-'}</p>
                <p className="text-xs text-[#666666]">Approachable</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-medium">{winner.avg_attractive?.toFixed(1) || '-'}</p>
                <p className="text-xs text-[#666666]">Attractive</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Ranked Photos */}
        {ranked.length > 1 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-8"
          >
            <h3 className="text-sm text-[#666666] uppercase tracking-wider mb-3">
              Ranking
            </h3>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {ranked.slice(1).map((photo, index) => (
                <div key={photo.photo_id} className="flex-shrink-0 relative">
                  <img
                    src={photos[photo.photo_id]?.preview || `${API}/files/${photos[photo.photo_id]?.storage_path}`}
                    alt={`Ranked ${index + 2}`}
                    className="w-20 h-28 object-cover rounded-[12px] border border-[#E5E5E5]"
                    onError={(e) => { e.target.src = 'https://via.placeholder.com/80x112?text=Photo'; }}
                  />
                  <div className="absolute bottom-1 left-1 bg-white/90 px-1.5 py-0.5 rounded-full text-xs font-medium">
                    #{index + 2}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Comments */}
        {winner?.comments?.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-8"
          >
            <h3 className="text-sm text-[#666666] uppercase tracking-wider mb-3 flex items-center gap-2">
              <MessageSquare size={14} />
              What people said
            </h3>
            <div className="space-y-3">
              {winner.comments.slice(0, 5).map((comment, index) => (
                <div key={index} className="card flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#F7F7F5] flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-medium">
                      {String.fromCharCode(65 + index)}
                    </span>
                  </div>
                  <p className="text-sm text-[#1A1A1A] flex-1">{comment}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Tags */}
        {winner?.tags?.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mb-8"
          >
            <h3 className="text-sm text-[#666666] uppercase tracking-wider mb-3">
              Common feedback
            </h3>
            <div className="flex flex-wrap gap-2">
              {[...new Set(winner.tags)].slice(0, 6).map((tag, index) => (
                <span key={index} className="badge badge-gray">{tag}</span>
              ))}
            </div>
          </motion.div>
        )}

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <button
            onClick={() => navigate(job.type === 'best-shot' ? '/profile-analysis' : '/dashboard')}
            className="btn-pill btn-primary w-full"
            data-testid="next-cta"
          >
            {job.type === 'best-shot' ? 'Try Profile Analysis' : 'Back to Dashboard'}
          </button>
        </motion.div>
      </div>
    </div>
  );
};

export default Results;
