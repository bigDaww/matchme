import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Upload, X, Image } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth, API } from '../App';

const ProfileAnalysis = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [photos, setPhotos] = useState([]);
  const [bio, setBio] = useState('');
  const [promptAnswer, setPromptAnswer] = useState('');
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(async (files) => {
    const validFiles = Array.from(files).filter(f => 
      ['image/jpeg', 'image/png', 'image/jpg'].includes(f.type) && f.size <= 10 * 1024 * 1024
    );

    if (validFiles.length + photos.length > 6) {
      toast.error('Maximum 6 photos allowed');
      return;
    }

    setUploading(true);
    
    for (const file of validFiles) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API}/upload`, formData, {
          withCredentials: true,
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        setPhotos(prev => [...prev, {
          photo_id: response.data.photo_id,
          storage_path: response.data.storage_path,
          preview: URL.createObjectURL(file)
        }]);
      } catch (error) {
        toast.error(`Failed to upload ${file.name}`);
      }
    }
    
    setUploading(false);
  }, [photos.length]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const removePhoto = (index) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (photos.length < 4) {
      toast.error('Upload at least 4 photos');
      return;
    }

    if ((user?.credits || 0) < 2) {
      toast.error('Not enough credits (need 2)');
      navigate('/pricing');
      return;
    }

    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/jobs/profile-analysis`, {
        photo_ids: photos.map(p => p.photo_id),
        bio: bio || null,
        prompt_answer: promptAnswer || null
      }, { withCredentials: true });
      
      toast.success('Profile submitted for analysis!');
      navigate(`/waiting/${response.data.job_id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button 
          onClick={() => navigate('/dashboard')}
          className="p-2 -ml-2"
          data-testid="back-btn"
        >
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          Profile Analysis
        </h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 px-6 py-6 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="text-[#666666] text-center mb-6">
            Upload 4-6 photos plus your bio for a complete profile review.
          </p>

          {/* Drop Zone */}
          {photos.length < 6 && (
            <div
              className={`drop-zone mb-6 ${dragOver ? 'dragging' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input').click()}
              data-testid="drop-zone"
            >
              <input
                id="file-input"
                type="file"
                accept="image/jpeg,image/png"
                multiple
                onChange={(e) => handleFiles(e.target.files)}
                className="hidden"
              />
              {uploading ? (
                <div className="w-8 h-8 border-2 border-[#1A1A1A] border-t-transparent rounded-full animate-spin mx-auto" />
              ) : (
                <>
                  <Upload size={32} className="mx-auto mb-3 text-[#666666]" strokeWidth={1.5} />
                  <p className="text-[#1A1A1A] font-medium mb-1">Drop photos here</p>
                  <p className="text-sm text-[#666666]">or tap to browse • JPG/PNG, max 10MB</p>
                </>
              )}
            </div>
          )}

          {/* Photo Grid */}
          {photos.length > 0 && (
            <div className="grid grid-cols-3 gap-2 mb-6">
              {photos.map((photo, index) => (
                <motion.div
                  key={photo.photo_id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="relative"
                >
                  <img
                    src={photo.preview}
                    alt={`Photo ${index + 1}`}
                    className="aspect-[3/4] object-cover rounded-[12px] border border-[#E5E5E5] w-full"
                  />
                  <button
                    onClick={() => removePhoto(index)}
                    className="absolute top-1 right-1 w-6 h-6 bg-white rounded-full shadow-md flex items-center justify-center"
                    data-testid={`remove-photo-${index}`}
                  >
                    <X size={12} />
                  </button>
                </motion.div>
              ))}
            </div>
          )}

          <p className="text-center text-sm text-[#666666] mb-6">
            {photos.length}/6 photos • Need at least 4
          </p>

          {/* Bio */}
          <div className="mb-6">
            <label className="text-sm text-[#666666] uppercase tracking-wider mb-2 block">
              Your Bio (optional)
            </label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Paste your dating app bio here..."
              className="w-full p-4 rounded-[12px] bg-[#F7F7F5] border-none resize-none h-24 outline-none focus:ring-2 focus:ring-[#C9B8E8]"
              data-testid="bio-input"
            />
          </div>

          {/* Prompt Answer */}
          <div className="mb-6">
            <label className="text-sm text-[#666666] uppercase tracking-wider mb-2 block">
              Prompt Answer (optional)
            </label>
            <textarea
              value={promptAnswer}
              onChange={(e) => setPromptAnswer(e.target.value)}
              placeholder="Paste one of your prompt answers..."
              className="w-full p-4 rounded-[12px] bg-[#F7F7F5] border-none resize-none h-24 outline-none focus:ring-2 focus:ring-[#C9B8E8]"
              data-testid="prompt-input"
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={photos.length < 4 || submitting}
            className={`btn-pill w-full ${
              photos.length >= 4 ? 'btn-primary' : 'btn-secondary opacity-50'
            }`}
            data-testid="submit-btn"
          >
            {submitting ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              `Get Profile Analysis (2 credits)`
            )}
          </button>

          <p className="text-center text-xs text-[#666666] mt-4">
            You have {user?.credits || 0} credits
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default ProfileAnalysis;
