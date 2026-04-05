import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Check, Star, Zap, Crown } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth, API } from '../App';

const Pricing = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handlePurchase = async (packageId) => {
    if (!user) {
      navigate('/auth');
      return;
    }

    try {
      const response = await axios.post(`${API}/payments/checkout`, {
        package_id: packageId,
        origin_url: window.location.origin
      }, { withCredentials: true });

      window.location.href = response.data.url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start checkout');
    }
  };

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: '$0',
      period: 'forever',
      icon: Star,
      features: [
        '3 credits on signup',
        '1 Best Shot review',
        'Rate 5 photos = 1 credit',
        'Max 5 earned credits/day',
        'Results in 24 hours'
      ],
      cta: 'Current Plan',
      disabled: true,
      highlight: false
    },
    {
      id: 'priority_pass',
      name: 'Priority Pass',
      price: '$9',
      period: 'one-time',
      icon: Zap,
      features: [
        '5 bonus credits',
        'Priority queue',
        'Results in 2 hours',
        'No subscription',
        'Use anytime'
      ],
      cta: 'Get Priority Pass',
      disabled: false,
      highlight: true
    },
    {
      id: 'pro_monthly',
      name: 'Pro',
      price: '$19',
      period: '/month',
      icon: Crown,
      features: [
        'Unlimited Best Shots',
        '4 Profile Analyses/month',
        'Always priority queue',
        'Results in 2 hours',
        'Cancel anytime'
      ],
      cta: 'Go Pro',
      disabled: false,
      highlight: false
    }
  ];

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="font-heading text-xl" style={{ fontFamily: 'Georgia, serif' }}>
          Pricing
        </h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 px-6 py-6 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h2 
            className="font-heading text-2xl mb-2"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Get more matches
          </h2>
          <p className="text-[#666666]">
            Choose the plan that works for you
          </p>
        </motion.div>

        <div className="space-y-4">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`card relative ${plan.highlight ? 'ring-2 ring-[#C9B8E8]' : ''}`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 badge badge-lilac">
                  Most Popular
                </div>
              )}

              <div className="flex items-start gap-4 mb-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  plan.highlight ? 'bg-[#C9B8E8]' : 'bg-[#F7F7F5]'
                }`}>
                  <plan.icon size={24} strokeWidth={1.5} />
                </div>
                <div className="flex-1">
                  <h3 className="font-heading text-lg" style={{ fontFamily: 'Georgia, serif' }}>
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-medium">{plan.price}</span>
                    <span className="text-sm text-[#666666]">{plan.period}</span>
                  </div>
                </div>
              </div>

              <ul className="space-y-2 mb-4">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm">
                    <Check size={16} className="text-[#6B7E4A]" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => !plan.disabled && handlePurchase(plan.id)}
                disabled={plan.disabled || (user?.tier === 'pro' && plan.id === 'pro_monthly')}
                className={`btn-pill w-full ${
                  plan.disabled || (user?.tier === 'pro' && plan.id === 'pro_monthly')
                    ? 'btn-secondary opacity-50 cursor-not-allowed'
                    : plan.highlight ? 'btn-primary' : 'btn-secondary'
                }`}
                data-testid={`buy-${plan.id}`}
              >
                {user?.tier === 'pro' && plan.id === 'pro_monthly' ? 'Current Plan' : plan.cta}
              </button>
            </motion.div>
          ))}
        </div>

        <p className="text-center text-xs text-[#666666] mt-8">
          Secure payment powered by Stripe
        </p>
      </div>
    </div>
  );
};

export default Pricing;
