import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Terms = () => {
  const navigate = useNavigate();

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          Terms of Service
        </h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 px-6 py-6 overflow-y-auto">
        <div className="prose prose-sm max-w-none">
          <p className="text-[#666666] text-sm mb-6">Last updated: January 2026</p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            1. Acceptance of Terms
          </h2>
          <p className="text-[#666666] mb-6">
            By accessing or using MatchMe, you agree to be bound by these Terms of Service 
            and our Privacy Policy.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            2. Use of Service
          </h2>
          <p className="text-[#666666] mb-6">
            You must be at least 18 years old to use this service. You agree to provide accurate 
            information and to use the service only for its intended purpose.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            3. User Content
          </h2>
          <p className="text-[#666666] mb-6">
            You retain ownership of photos you upload. By uploading, you grant us a license to 
            display them to other users for rating purposes. You must not upload inappropriate 
            or illegal content.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            4. Credits & Payments
          </h2>
          <p className="text-[#666666] mb-6">
            Credits are non-refundable and non-transferable. Prices may change with notice. 
            All payments are processed securely through Stripe.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            5. Community Guidelines
          </h2>
          <p className="text-[#666666] mb-6">
            Be respectful when rating others. Harassment, hate speech, or inappropriate comments 
            will result in account termination.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            6. Limitation of Liability
          </h2>
          <p className="text-[#666666] mb-6">
            MatchMe is provided "as is" without warranties. We are not liable for any damages 
            arising from your use of the service.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            7. Changes to Terms
          </h2>
          <p className="text-[#666666] mb-6">
            We may update these terms at any time. Continued use of the service constitutes 
            acceptance of the updated terms.
          </p>

          <h2 className="font-heading text-lg mb-3" style={{ fontFamily: 'Georgia, serif' }}>
            8. Contact
          </h2>
          <p className="text-[#666666] mb-6">
            For questions about these Terms, contact us at legal@matchme.app
          </p>
        </div>
      </div>
    </div>
  );
};

export default Terms;
