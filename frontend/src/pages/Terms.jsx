import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Terms = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FFFFFD]">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          Terms of Service
        </h1>
        <div className="w-10" />
      </div>

      <div className="px-6 md:px-12 lg:px-24 py-8 md:py-12">
        <div className="max-w-[800px] mx-auto">
          <p className="text-[#666666] text-sm mb-8">Last updated: January 2026</p>

          <div className="space-y-8">
            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                1. Acceptance of Terms
              </h2>
              <p className="text-[#666666] leading-relaxed">
                By accessing or using MatchMe, you agree to be bound by these Terms of Service 
                and our Privacy Policy.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                2. Use of Service
              </h2>
              <p className="text-[#666666] leading-relaxed">
                You must be at least 18 years old to use this service. You agree to provide accurate 
                information and to use the service only for its intended purpose.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                3. User Content
              </h2>
              <p className="text-[#666666] leading-relaxed">
                You retain ownership of photos you upload. By uploading, you grant us a license to 
                display them to other users for rating purposes. You must not upload inappropriate 
                or illegal content.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                4. Credits & Payments
              </h2>
              <p className="text-[#666666] leading-relaxed">
                Credits are non-refundable and non-transferable. Prices may change with notice. 
                All payments are processed securely through Stripe.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                5. Community Guidelines
              </h2>
              <p className="text-[#666666] leading-relaxed">
                Be respectful when rating others. Harassment, hate speech, or inappropriate comments 
                will result in account termination.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                6. Limitation of Liability
              </h2>
              <p className="text-[#666666] leading-relaxed">
                MatchMe is provided "as is" without warranties. We are not liable for any damages 
                arising from your use of the service.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                7. Changes to Terms
              </h2>
              <p className="text-[#666666] leading-relaxed">
                We may update these terms at any time. Continued use of the service constitutes 
                acceptance of the updated terms.
              </p>
            </section>

            <section>
              <h2 className="text-xl mb-4" style={{ fontFamily: 'Georgia, serif' }}>
                8. Contact
              </h2>
              <p className="text-[#666666] leading-relaxed">
                For questions about these Terms, contact us at legal@matchme.app
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Terms;
