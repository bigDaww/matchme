import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Upload, X, Image } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth, API } from '../App';
import Layout from '../components/Layout';

const BestShot = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [photos, setPhotos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(async (files) => {
    const validFiles = Array.from(files).filter(f => 
      ['image/jpeg', 'image/png', 'image/jpg'].includes(f.type) && f.size <= 10 * 1024 * 1024
    );

    if (validFiles.length + photos.length > 10) {
      toast.error('Maximum 10 photos allowed');
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
    if (photos.length < 3) {
      toast.error('Upload at least 3 photos');
      return;
    }

    if (user?.tier !== 'pro' && (user?.credits || 0) < 1) {
      toast.error('Not enough credits');
      navigate('/pricing');
      return;
    }

    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/jobs/best-shot`, {
        photo_ids: photos.map(p => p.photo_id)
      }, { withCredentials: true });
      
      toast.success('Photos submitted for review!');
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
            Best Shot
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
                Upload 3-10 photos and real people will tell you which one makes the best first impression.
              </p>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Upload Section */}
                <div className="lg:col-span-2">
                  {/* Drop Zone */}
                  {photos.length < 10 && (
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

                  {/* Photo Grid - 3 columns on desktop */}
                  {photos.length > 0 && (
                    <div className="photo-grid-responsive mb-6">
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
                            className="photo-tile"
                          />
                          <button
                            onClick={() => removePhoto(index)}
                            className="absolute top-2 right-2 w-8 h-8 bg-white rounded-full shadow-md flex items-center justify-center hover:bg-gray-100"
                            data-testid={`remove-photo-${index}`}
                          >
                            <X size={16} />
                          </button>
                          <div className="absolute bottom-2 left-2 bg-white/90 px-2 py-1 rounded-full text-xs font-medium">
                            #{index + 1}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {/* Empty State */}
                  {photos.length === 0 && !uploading && (
                    <div className="text-center py-8 lg:py-12">
                      <Image size={48} className="mx-auto mb-4 text-[#E5E5E5]" strokeWidth={1} />
                      <p className="text-[#666666]">No photos yet</p>
                    </div>
                  )}
                </div>

                {/* Sidebar - Submit Section */}
                <div className="lg:sticky lg:top-24 lg:self-start">
                  <div className="card">
                    <h3 className="text-lg mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                      Ready to submit?
                    </h3>
                    
                    {/* Photo Count */}
                    <p className="text-sm text-[#666666] mb-4">
                      {photos.length}/10 photos uploaded
                      {photos.length < 3 && <span className="block text-[#E5533C]">Need at least 3</span>}
                    </p>

                    {user?.tier !== 'pro' && (
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                          <span>Cost</span>
                          <span className="font-medium">1 credit</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>Your balance</span>
                          <span className="font-medium">{user?.credits || 0} credits</span>
                        </div>
                      </div>
                    )}
                    {user?.tier === 'pro' && (
                      <p className="text-sm text-[#666666] mb-2">Included with your Pro plan</p>
                    )}

                    <hr className="my-4 border-[#E5E5E5]" />

                    {/* Submit Button */}
                    <button
                      onClick={handleSubmit}
                      disabled={photos.length < 3 || submitting}
                      className={`btn-pill w-full ${
                        photos.length >= 3 ? 'btn-primary' : 'btn-secondary opacity-50'
                      }`}
                      data-testid="submit-btn"
                    >
                      {submitting ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        `Submit for Review`
                      )}
                    </button>

                    <p className="text-center text-xs text-[#666666] mt-4">
                      Results delivered within {user?.tier === 'free' || !user?.tier ? '24 hours' : '2-4 hours'}
                    </p>
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

export default BestShot;
