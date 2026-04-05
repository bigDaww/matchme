import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Flag, SkipForward } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API } from '../App';

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

      if (response.data.earned_credit) {
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
      <div className="app-container flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#1A1A1A] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!photo) {
    return (
      <div className="app-container">
        <div className="top-bar border-b border-[#E5E5E5]">
          <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2" data-testid="back-btn">
            <ArrowLeft size={24} strokeWidth={1.5} />
          </button>
          <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>Rate Others</h1>
          <div className="w-10" />
        </div>
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
          <p className="text-[#666666] mb-4">No photos to rate right now.</p>
          <p className="text-sm text-[#666666] mb-6">Check back later when more users submit their profiles for review.</p>
          <button onClick={() => navigate('/dashboard')} className="btn-pill btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate('/dashboard')} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <div className="flex items-center gap-2">
          {[...Array(5)].map((_, i) => (
            <div 
              key={i}
              className={`progress-dot ${i < (photo?.progress || 0) ? 'active' : ''}`}
            />
          ))}
        </div>
        <div className="badge badge-lilac text-xs">
          5 = 1 credit
        </div>
      </div>

      <div className="flex-1 px-6 py-4 overflow-y-auto pb-32">
        {/* Photo */}
        <motion.div
          key={photo.photo_id}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-6"
        >
          <img
            src={`${API}/files/${photo.storage_path}`}
            alt="Profile to rate"
            className="photo-tile mx-auto max-h-[350px] w-auto"
            data-testid="rate-photo"
          />
        </motion.div>

        {/* Sliders */}
        <div className="space-y-6 mb-6">
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
        <div className="mb-6">
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
        <div className="mb-6">
          <label className="text-sm text-[#666666] mb-2 block">
            What would make this profile stronger? *
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Be kind and constructive..."
            className="w-full p-4 rounded-[12px] bg-[#F7F7F5] border-none resize-none h-24 outline-none focus:ring-2 focus:ring-[#C9B8E8]"
            data-testid="comment-input"
          />
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] bg-[#FFFFFD] border-t border-[#E5E5E5] p-4">
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
            className="flex-2 btn-pill btn-primary flex-[2]"
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
          className="w-full text-center text-sm text-[#666666] mt-3 hover:text-[#E5533C]"
          data-testid="report-btn"
        >
          <Flag size={14} className="inline mr-1" />
          Report Photo
        </button>
      </div>
    </div>
  );
};

export default RateOthers;
