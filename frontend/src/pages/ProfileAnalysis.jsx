import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Upload, X, Image } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth, API } from '../App';
import Layout from '../components/Layout';

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

    if (validFiles.length + photos.length > 3) {
      toast.error('Maximum 3 photos allowed');
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
    if (photos.length < 1) {
      toast.error('Upload at least 1 photo');
      return;
    }

    if (user?.tier !== 'pro' && (user?.credits || 0) < 2) {
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
    <Layout>
      <div className="min-h-screen">
        {/* Top Bar */}
        <div className="top-bar border-b border-[#E5E5E5]">
          <button 
            onClick={() => navigate('/dashboard')}
            className="p-2 -ml-2 lg:hidden"
            data-testid="back-btn"
          >
            <ArrowLeft size={24} strokeWidth={1.5} />
          </button>
          <h1 className="text-xl lg:text-2xl" style={{ fontFamily: 'Georgia, serif' }}>
            Profile Analysis
          </h1>
          <div className="w-10 lg:hidden" />
        </div>

        <div className="px-6 md:px-8 lg:px-12 py-6 md:py-8">
          <div className="max-w-[1200px] mx-auto lg:mx-0">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <p className="text-[#666666] text-center lg:text-left mb-6 max-w-2xl">
                Upload 1-3 photos plus your bio for a complete profile review.
              </p>

              <div className="two-col-layout">
                {/* Left Column - Photos */}
                <div className="col-left">
                  {/* Drop Zone */}
                  {photos.length < 3 && (
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
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
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
                            className="aspect-[3/4] object-cover rounded-[16px] border border-[#E5E5E5] w-full"
                          />
                          <button
                            onClick={() => removePhoto(index)}
                            className="absolute top-2 right-2 w-7 h-7 bg-white rounded-full shadow-md flex items-center justify-center hover:bg-gray-100"
                            data-testid={`remove-photo-${index}`}
                          >
                            <X size={14} />
                          </button>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  <p className="text-center lg:text-left text-sm text-[#666666] mb-6">
                    {photos.length}/3 photos • Need at least 1
                  </p>
                </div>

                {/* Right Column - Bio & Prompts */}
                <div className="col-right space-y-6">
                  {/* Bio */}
                  <div>
                    <label className="text-sm text-[#666666] uppercase tracking-wider mb-2 block">
                      Your Bio (optional)
                    </label>
                    <textarea
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      placeholder="Paste your dating app bio here..."
                      className="w-full p-4 rounded-[16px] bg-[#F7F7F5] border-none resize-none h-32 outline-none focus:ring-2 focus:ring-[#C9B8E8]"
                      data-testid="bio-input"
                    />
                  </div>

                  {/* Prompt Answer */}
                  <div>
                    <label className="text-sm text-[#666666] uppercase tracking-wider mb-2 block">
                      Prompt Answer (optional)
                    </label>
                    <textarea
                      value={promptAnswer}
                      onChange={(e) => setPromptAnswer(e.target.value)}
                      placeholder="Paste one of your prompt answers..."
                      className="w-full p-4 rounded-[16px] bg-[#F7F7F5] border-none resize-none h-32 outline-none focus:ring-2 focus:ring-[#C9B8E8]"
                      data-testid="prompt-input"
                    />
                  </div>

                  {/* Submit Card */}
                  <div className="card">
                    <h3 className="text-lg mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                      Ready to submit?
                    </h3>
                    
                    {user?.tier !== 'pro' ? (
                      <div className="space-y-3 mb-4">
                        <div className="flex justify-between text-sm">
                          <span>Cost</span>
                          <span className="font-medium">2 credits</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>Your balance</span>
                          <span className="font-medium">{Math.floor(user?.credits || 0)} credits</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-[#666666] mb-4">Included with your Pro plan</p>
                    )}

                    {/* Submit Button */}
                    <button
                      onClick={handleSubmit}
                      disabled={photos.length < 1 || submitting}
                      className={`btn-pill w-full ${
                        photos.length >= 1 ? 'btn-primary' : 'btn-secondary opacity-50'
                      }`}
                      data-testid="submit-btn"
                    >
                      {submitting ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        `Get Profile Analysis`
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ProfileAnalysis;
