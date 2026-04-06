import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Flag, SkipForward, Infinity } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API } from '../App';
import Layout from '../components/Layout';

const RateOthers = () => {
  const navigate = useNavigate();
  const [photo, setPhoto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [ratings, setRatings] = useState({
    confident: 3,
    approachable: 3,
    attractive: 3
  });
  const [selectedTags, setSelectedTags] = useState([]);
  const [comment, setComment] = useState('');

  const tags = [
    'Best first photo',
    'Too posed',
    'Good smile',
    'Bad lighting',
    'Looks confident',
    'Feels natural',
    'Too blurry',
    'Great background'
  ];

  useEffect(() => {
    fetchNextPhoto();
  }, []);

  const fetchNextPhoto = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/rate/next`, { withCredentials: true });
      setPhoto(response.data);
      setRatings({ confident: 3, approachable: 3, attractive: 3 });
      setSelectedTags([]);
      setComment('');
    } catch (error) {
      if (error.response?.status === 404) {
        setPhoto(null);
      } else {
        toast.error(error.response?.data?.detail || 'Failed to load photo');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!comment.trim()) {
      toast.error('Please add a comment');
      return;
    }

    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/rate/submit`, {
        photo_id: photo.photo_id,
        confident: ratings.confident,
        approachable: ratings.approachable,
        attractive: ratings.attractive,
        tags: selectedTags,
        comment: comment.trim()
      }, { withCredentials: true });

      if (response.data.is_pro) {
        toast.success('Thanks for helping the community!');
      } else if (response.data.earned_credit) {
        toast.success('You earned 1 credit!');
      } else {
        toast.success(`Rating submitted! ${response.data.ratings_until_credit} more until next credit`);
      }

      fetchNextPhoto();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit rating');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReport = async () => {
    if (!photo) return;
    try {
      await axios.post(`${API}/rate/report?photo_id=${photo.photo_id}`, {}, { withCredentials: true });
      toast.success('Photo reported');
      fetchNextPhoto();
    } catch (error) {
      toast.error('Failed to report');
    }
  };

  const toggleTag = (tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
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

  if (!photo) {
    return (
      <Layout>
        <div className="min-h-screen">
          <div className="top-bar border-b border-[#E5E5E5]">
            <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2 lg:hidden" data-testid="back-btn">
              <ArrowLeft size={24} strokeWidth={1.5} />
            </button>
            <h1 className="text-xl lg:text-2xl" style={{ fontFamily: 'Georgia, serif' }}>Rate Others</h1>
            <div className="w-10 lg:hidden" />
          </div>
          <div className="flex-1 flex flex-col items-center justify-center px-6 py-20 text-center">
            <p className="text-[#666666] mb-4 text-lg">No photos to rate right now.</p>
            <p className="text-sm text-[#666666] mb-6 max-w-md">Check back later when more users submit their profiles for review.</p>
            <button onClick={() => navigate('/dashboard')} className="btn-pill btn-primary">
              Back to Dashboard
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const isPro = photo.is_pro;

  return (
    <Layout>
      <div className="min-h-screen pb-nav lg:pb-0">
        {/* Top Bar */}
        <div className="top-bar border-b border-[#E5E5E5]">
          <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2 lg:hidden" data-testid="back-btn">
            <ArrowLeft size={24} strokeWidth={1.5} />
          </button>
          {isPro ? (
            <div className="badge badge-lilac text-xs">
              <Infinity size={12} className="mr-1" />
              Pro
            </div>
          ) : (
            <div className="flex items-center gap-2">
              {[...Array(5)].map((_, i) => (
                <div 
                  key={i}
                  className={`progress-dot ${i < (photo?.progress || 0) ? 'active' : ''}`}
                />
              ))}
            </div>
          )}
          {!isPro && (
            <div className="badge badge-lilac text-xs">
              5 = 1 credit
            </div>
          )}
          {isPro && <div className="w-10" />}
        </div>

        <div className="px-6 md:px-8 lg:px-12 py-6">
          <div className="max-w-[1200px] mx-auto lg:mx-0">
            {/* Desktop: Photo on left, controls on right */}
            <div className="rate-layout">
              {/* Photo */}
              <div className="rate-photo">
                <motion.div
                  key={photo.photo_id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <img
                    src={photo.url}
                    alt="Profile to rate"
                    className="photo-tile mx-auto lg:mx-0 max-h-[400px] lg:max-h-[500px] w-auto"
                    data-testid="rate-photo"
                  />
                </motion.div>
              </div>

              {/* Rating Controls */}
              <div className="rate-controls space-y-6">
                {/* Sliders */}
                <div className="space-y-5">
                  {[
                    { key: 'confident', label: 'Confident' },
                    { key: 'approachable', label: 'Approachable' },
                    { key: 'attractive', label: 'Attractive' }
                  ].map(({ key, label }) => (
                    <div key={key}>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-[#666666]">{label}</span>
                        <span className="text-sm font-medium">{ratings[key]}/5</span>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={ratings[key]}
                        onChange={(e) => setRatings(prev => ({ ...prev, [key]: parseInt(e.target.value) }))}
                        className="w-full"
                        data-testid={`slider-${key}`}
                      />
                    </div>
                  ))}
                </div>

                {/* Tags */}
                <div>
                  <p className="text-sm text-[#666666] mb-3">Quick feedback (optional)</p>
                  <div className="flex flex-wrap gap-2">
                    {tags.map(tag => (
                      <button
                        key={tag}
                        onClick={() => toggleTag(tag)}
                        className={`tag-chip ${selectedTags.includes(tag) ? 'selected' : ''}`}
                        data-testid={`tag-${tag.toLowerCase().replace(/\s/g, '-')}`}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Comment */}
                <div>
                  <label className="text-sm text-[#666666] mb-2 block">
                    What would make this profile stronger? *
                  </label>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Be kind and constructive..."
                    className="w-full p-4 rounded-[16px] bg-[#F7F7F5] border-none resize-none h-24 outline-none focus:ring-2 focus:ring-[#C9B8E8]"
                    data-testid="comment-input"
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={fetchNextPhoto}
                    className="flex-1 btn-pill btn-secondary flex items-center justify-center gap-2"
                    data-testid="skip-btn"
                  >
                    <SkipForward size={18} />
                    Skip
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting || !comment.trim()}
                    className="flex-[2] btn-pill btn-primary"
                    data-testid="submit-rating-btn"
                  >
                    {submitting ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      'Submit Review'
                    )}
                  </button>
                </div>

                <button
                  onClick={handleReport}
                  className="w-full text-center text-sm text-[#666666] hover:text-[#E5533C]"
                  data-testid="report-btn"
                >
                  <Flag size={14} className="inline mr-1" />
                  Report Photo
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default RateOthers;
