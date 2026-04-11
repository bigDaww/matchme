import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle } from 'lucide-react';

const PaymentSuccess = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FFFFFD] flex items-center justify-center px-6 py-12">
      <div className="text-center max-w-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <CheckCircle size={80} className="mx-auto mb-6 text-[#6B7E4A]" />
          <h2 
            className="text-2xl md:text-3xl mb-3"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Payment successful!
          </h2>
          <p className="text-[#666666] mb-8">
            Your subscription has been activated.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-pill btn-primary"
            data-testid="continue-btn"
          >
            Continue to Dashboard
          </button>
        </motion.div>
      </div>
    </div>
  );
};

export default PaymentSuccess;
