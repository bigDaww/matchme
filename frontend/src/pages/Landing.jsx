import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Camera, Sparkles, MessageSquare, ChevronRight, ArrowRight } from 'lucide-react';

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Camera,
      title: 'Best Shot',
      description: 'Find out which photo makes the best first impression'
    },
    {
      icon: Sparkles,
      title: 'Profile Analysis',
      description: 'Get detailed feedback on your entire profile'
    },
    {
      icon: MessageSquare,
      title: 'Bio Rewriter',
      description: 'Optimize your bio for more matches'
    }
  ];

  return (
    <div className="min-h-screen bg-[#FFFFFD]">
      {/* Hero Section - Full Width */}
      <section className="w-full px-6 md:px-12 lg:px-24 py-12 md:py-20 lg:py-28">
        <div className="max-w-[1200px] mx-auto">
          <div className="flex flex-col lg:flex-row lg:items-center lg:gap-16">
            {/* Hero Text */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="flex-1 text-center lg:text-left mb-10 lg:mb-0"
            >
              <h1 
                className="text-4xl md:text-5xl lg:text-6xl leading-tight mb-6 text-[#1A1A1A]"
                style={{ fontFamily: 'Georgia, serif' }}
              >
                Your best photo is already on your phone.
              </h1>
              <p className="text-[#666666] text-lg md:text-xl mb-8 max-w-lg mx-auto lg:mx-0">
                Real people tell you which ones to use — and which to delete.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <button
                  data-testid="get-started-btn"
                  onClick={() => navigate('/auth')}
                  className="btn-pill btn-primary text-lg px-8"
                >
                  Get My Profile Reviewed — Free
                  <ArrowRight size={20} className="ml-2" />
                </button>
                <button
                  onClick={() => navigate('/pricing')}
                  className="btn-pill btn-secondary"
                  data-testid="view-pricing-btn"
                >
                  View Pricing
                </button>
              </div>

              {/* Social Proof */}
              <p className="text-[#666666] text-sm mt-8">
                Join <span className="font-medium text-[#1A1A1A]">2,000+</span> people getting more matches
              </p>
            </motion.div>

            {/* Hero Image */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="flex-shrink-0 flex justify-center lg:justify-end"
            >
              <img
                src="https://images.unsplash.com/photo-1620342242548-f49a774555a4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1OTN8MHwxfHNlYXJjaHwzfHxhdHRyYWN0aXZlJTIwcGVyc29uJTIwc21pbGluZyUyMGNhbmRpZCUyMHBvcnRyYWl0JTIwb3V0ZG9vcnxlbnwwfHx8fDE3NzU0MjQxMDB8MA&ixlib=rb-4.1.0&q=85"
                alt="Profile example"
                className="photo-tile w-[280px] md:w-[320px] lg:w-[380px]"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="w-full px-6 md:px-12 lg:px-24 py-12 md:py-16 bg-[#F7F7F5]">
        <div className="max-w-[1200px] mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-2xl md:text-3xl text-center mb-10 md:mb-12"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            How it works
          </motion.h2>

          <div className="feature-grid">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
                className="card flex flex-col items-center text-center lg:p-8"
              >
                <div className="w-16 h-16 rounded-full bg-[#C9B8E8] flex items-center justify-center mb-4">
                  <feature.icon size={32} strokeWidth={1.5} className="text-[#1A1A1A]" />
                </div>
                <h3 
                  className="text-xl mb-2 text-[#1A1A1A]"
                  style={{ fontFamily: 'Georgia, serif' }}
                >
                  {feature.title}
                </h3>
                <p className="text-[#666666]">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full px-6 md:px-12 lg:px-24 py-16 md:py-24">
        <div className="max-w-[600px] mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <h2 
              className="text-2xl md:text-3xl mb-4"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              Ready to get more matches?
            </h2>
            <p className="text-[#666666] mb-8">
              Start with 3 free credits. No credit card required.
            </p>
            <button
              onClick={() => navigate('/auth')}
              className="btn-pill btn-primary text-lg"
              data-testid="cta-get-started"
            >
              Get Started Free
            </button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full px-6 md:px-12 lg:px-24 py-8 border-t border-[#E5E5E5]">
        <div className="max-w-[1200px] mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-[#666666]">© 2026 MatchMe. All rights reserved.</p>
          <div className="flex gap-6">
            <button 
              onClick={() => navigate('/privacy')}
              className="text-sm text-[#666666] hover:text-[#1A1A1A]"
              data-testid="privacy-link"
            >
              Privacy
            </button>
            <button 
              onClick={() => navigate('/terms')}
              className="text-sm text-[#666666] hover:text-[#1A1A1A]"
              data-testid="terms-link"
            >
              Terms
            </button>
            <button 
              onClick={() => navigate('/pricing')}
              className="text-sm text-[#666666] hover:text-[#1A1A1A]"
              data-testid="pricing-link"
            >
              Pricing
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
