import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Camera, Sparkles, MessageSquare, ChevronRight } from 'lucide-react';

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
    <div className="app-container">
      <div className="flex-1 px-6 py-12">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <h1 
            className="font-heading text-4xl leading-tight mb-4 text-[#1A1A1A]"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Your best photo is already on your phone.
          </h1>
          <p className="text-[#666666] text-lg mb-8">
            Real people tell you which ones to use — and which to delete.
          </p>
          
          <button
            data-testid="get-started-btn"
            onClick={() => navigate('/auth')}
            className="btn-pill btn-primary w-full text-lg"
          >
            Get My Profile Reviewed — Free
          </button>
        </motion.div>

        {/* Hero Image */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mb-12"
        >
          <img
            src="https://images.unsplash.com/photo-1620342242548-f49a774555a4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1OTN8MHwxfHNlYXJjaHwzfHxhdHRyYWN0aXZlJTIwcGVyc29uJTIwc21pbGluZyUyMGNhbmRpZCUyMHBvcnRyYWl0JTIwb3V0ZG9vcnxlbnwwfHx8fDE3NzU0MjQxMDB8MA&ixlib=rb-4.1.0&q=85"
            alt="Profile example"
            className="photo-tile mx-auto max-w-[280px]"
          />
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="space-y-4 mb-12"
        >
          {features.map((feature, index) => (
            <div key={index} className="card flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-[#F7F7F5] flex items-center justify-center flex-shrink-0">
                <feature.icon size={24} strokeWidth={1.5} className="text-[#1A1A1A]" />
              </div>
              <div className="flex-1">
                <h3 className="font-heading text-lg text-[#1A1A1A]" style={{ fontFamily: 'Georgia, serif' }}>
                  {feature.title}
                </h3>
                <p className="text-[#666666] text-sm">{feature.description}</p>
              </div>
              <ChevronRight size={20} className="text-[#E5E5E5]" />
            </div>
          ))}
        </motion.div>

        {/* Social Proof */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="text-center"
        >
          <p className="text-[#666666] text-sm">
            Join <span className="font-medium text-[#1A1A1A]">2,000+</span> people getting more matches
          </p>
        </motion.div>
      </div>

      {/* Footer Links */}
      <div className="px-6 py-6 border-t border-[#E5E5E5] flex justify-center gap-6">
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
  );
};

export default Landing;
