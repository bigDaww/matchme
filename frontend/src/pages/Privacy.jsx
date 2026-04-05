import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Privacy = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FFFFFD]">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          Privacy Policy
        </h1>
        <div className="w-10" />
      </div>

      <div className="px-6 md:px-12 lg:px-24 py-8 md:py-12">
        <div className="max-w-[800px] mx-auto">
          <p className="text-[#666666] text-sm mb-8">Last updated: January 2026</p>

          <div className="space-y-8">
            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                1. Information We Collect
              </h2>
              <p className="text-[#666666] leading-relaxed">
                We collect information you provide directly, including your email address, profile photos, 
                and any feedback you submit. We also collect usage data to improve our service.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                2. How We Use Your Information
              </h2>
              <p className="text-[#666666] leading-relaxed">
                Your photos are shared with other users for rating purposes only. We use your information 
                to provide and improve our service, process payments, and communicate with you.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                3. Photo Storage & Security
              </h2>
              <p className="text-[#666666] leading-relaxed">
                Your photos are stored securely and are only shown to other users for rating. 
                We do not sell or share your photos with third parties for advertising purposes.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                4. Data Retention
              </h2>
              <p className="text-[#666666] leading-relaxed">
                We retain your data for as long as your account is active. You can request deletion 
                of your data at any time by contacting us.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                5. Your Rights
              </h2>
              <p className="text-[#666666] leading-relaxed">
                You have the right to access, correct, or delete your personal data. 
                You can also opt out of marketing communications at any time.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                6. Contact Us
              </h2>
              <p className="text-[#666666] leading-relaxed">
                If you have questions about this Privacy Policy, please contact us at privacy@matchme.app
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Privacy;
