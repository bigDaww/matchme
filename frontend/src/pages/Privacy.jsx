import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Privacy = () => {
  const navigate = useNavigate();

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          Privacy Policy
        </h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 px-6 py-6 overflow-y-auto">
        <div className="prose prose-sm max-w-none">
          <p className="text-[#666666] text-sm mb-6">Last updated: January 2026</p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            1. Information We Collect
          </h2>
          <p className="text-[#666666] mb-6">
            We collect information you provide directly, including your email address, profile photos, 
            and any feedback you submit. We also collect usage data to improve our service.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            2. How We Use Your Information
          </h2>
          <p className="text-[#666666] mb-6">
            Your photos are shared with other users for rating purposes only. We use your information 
            to provide and improve our service, process payments, and communicate with you.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            3. Photo Storage & Security
          </h2>
          <p className="text-[#666666] mb-6">
            Your photos are stored securely and are only shown to other users for rating. 
            We do not sell or share your photos with third parties for advertising purposes.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            4. Data Retention
          </h2>
          <p className="text-[#666666] mb-6">
            We retain your data for as long as your account is active. You can request deletion 
            of your data at any time by contacting us.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            5. Your Rights
          </h2>
          <p className="text-[#666666] mb-6">
            You have the right to access, correct, or delete your personal data. 
            You can also opt out of marketing communications at any time.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            6. Contact Us
          </h2>
          <p className="text-[#666666] mb-6">
            If you have questions about this Privacy Policy, please contact us at privacy@matchme.app
          </p>
        </div>
      </div>
    </div>
  );
};

export default Privacy;
