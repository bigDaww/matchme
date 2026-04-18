import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Check, Star, Zap } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth, API } from '../App';

const Pricing = () => {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(null);

  // Load Razorpay script on mount
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  const handleSubscribe = async (packageId) => {
    if (!user) {
      navigate('/auth');
      return;
    }

    if (packageId === 'free') {
      toast.info('You are already on the Free plan');
      return;
    }

    setLoading(packageId);
    try {
      // 1. Create subscription on backend
      const response = await axios.post(`${API}/payments/subscribe`, {
        package_id: packageId
      }, { withCredentials: true });

      const data = response.data;

      // 2. Open Razorpay Checkout modal
      const options = {
        key: data.razorpay_key_id,
        subscription_id: data.subscription_id,
        name: data.name,
        description: data.description,
        prefill: data.prefill,
        theme: {
          color: '#1A1A1A'
        },
        handler: async function (paymentResponse) {
          // 3. Verify payment on backend
          try {
            const verifyRes = await axios.post(`${API}/payments/verify`, {
              razorpay_payment_id: paymentResponse.razorpay_payment_id,
              razorpay_subscription_id: paymentResponse.razorpay_subscription_id,
              razorpay_signature: paymentResponse.razorpay_signature,
              package_id: packageId
            }, { withCredentials: true });

            toast.success(verifyRes.data.message || 'Subscription activated!');
            await refreshUser();
            navigate('/dashboard');
          } catch (verifyErr) {
            toast.error(verifyErr.response?.data?.detail || 'Payment verification failed');
          }
          setLoading(null);
        },
        modal: {
          ondismiss: function () {
            setLoading(null);
          }
        }
      };

      if (!window.Razorpay) {
        toast.error('Payment system is loading. Please try again.');
        setLoading(null);
        return;
      }

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response) {
        toast.error(response.error?.description || 'Payment failed');
        setLoading(null);
      });
      rzp.open();

    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start checkout');
      setLoading(null);
    }
  };

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: '₹0',
      period: 'forever',
      icon: Star,
      features: [
        '3 free credits on signup',
        'Earn credits by rating others',
        'Results as soon as 1 person reviews',
        'Reviewed by 3 real people'
      ],
      cta: user ? 'Current Plan' : 'Get Started',
      disabled: !!user,
      highlight: false
    },
    {
      id: 'priority',
      name: 'Priority',
      price: '₹749',
      period: '/month',
      icon: Zap,
      features: [
        '12 credits per month',
        'Results in 2–4 hours',
        'Reviewed by 7 real people',
        'Priority queue always on'
      ],
      cta: user?.tier === 'priority' ? 'Current Plan' : 'Subscribe',
      disabled: user?.tier === 'priority',
      highlight: true
    }
  ];

  return (
    <div className="min-h-screen bg-[#FFFFFD]">
      {/* Top Bar */}
      <div className="top-bar border-b border-[#E5E5E5]">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2" data-testid="back-btn">
          <ArrowLeft size={24} strokeWidth={1.5} />
        </button>
        <h1 className="text-xl lg:text-2xl" style={{ fontFamily: 'Georgia, serif' }}>
          Pricing
        </h1>
        <div className="w-10" />
      </div>

      <div className="px-6 md:px-12 lg:px-24 py-8 md:py-12">
        <div className="max-w-[1200px] mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10 md:mb-12"
          >
            <h2 
              className="text-2xl md:text-3xl lg:text-4xl mb-3"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              Get more matches
            </h2>
            <p className="text-[#666666] text-lg">
              Choose the plan that works for you
            </p>
          </motion.div>

          {/* Pricing Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 max-w-3xl mx-auto">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`card relative ${plan.highlight ? 'ring-2 ring-[#C9B8E8] md:scale-105' : ''}`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 badge badge-lilac">
                    Most Popular
                  </div>
                )}

                <div className="flex flex-col items-center text-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${
                    plan.highlight ? 'bg-[#C9B8E8]' : 'bg-[#F7F7F5]'
                  }`}>
                    <plan.icon size={32} strokeWidth={1.5} />
                  </div>
                  
                  <h3 className="text-xl mb-2" style={{ fontFamily: 'Georgia, serif' }}>
                    {plan.name}
                  </h3>
                  
                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-4xl font-medium">{plan.price}</span>
                    <span className="text-sm text-[#666666]">{plan.period}</span>
                  </div>

                  <ul className="space-y-3 mb-6 w-full">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <Check size={16} className="text-[#6B7E4A] flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => !plan.disabled && handleSubscribe(plan.id)}
                    disabled={plan.disabled || loading === plan.id}
                    className={`btn-pill w-full ${
                      plan.disabled
                        ? 'btn-secondary opacity-50 cursor-not-allowed'
                        : plan.highlight ? 'btn-primary' : 'btn-secondary'
                    }`}
                    data-testid={`buy-${plan.id}`}
                  >
                    {loading === plan.id ? (
                      <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    ) : (
                      plan.cta
                    )}
                  </button>
                </div>
              </motion.div>
            ))}
          </div>

          <p className="text-center text-sm text-[#666666] mt-10">
            Secure payment powered by Razorpay. Cancel anytime.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
