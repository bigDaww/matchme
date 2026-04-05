import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import axios from 'axios';
import { useAuth, API } from '../App';

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState('loading');
  const [paymentData, setPaymentData] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      pollPaymentStatus(sessionId);
    } else {
      setStatus('error');
    }
  }, [searchParams]);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setStatus('timeout');
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${sessionId}`, { withCredentials: true });
      setPaymentData(response.data);

      if (response.data.payment_status === 'paid') {
        setStatus('success');
        await refreshUser();
        return;
      } else if (response.data.status === 'expired') {
        setStatus('expired');
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      if (attempts < maxAttempts - 1) {
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
      } else {
        setStatus('error');
      }
    }
  };

  return (
    <div className="app-container flex items-center justify-center">
      <div className="px-6 py-12 text-center max-w-sm">
        {status === 'loading' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Loader size={48} className="mx-auto mb-4 animate-spin text-[#C9B8E8]" />
            <h2 
              className="font-heading text-2xl mb-2"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              Processing payment...
            </h2>
            <p className="text-[#666666]">Please wait while we confirm your purchase.</p>
          </motion.div>
        )}

        {status === 'success' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <CheckCircle size={64} className="mx-auto mb-4 text-[#6B7E4A]" />
            <h2 
              className="font-heading text-2xl mb-2"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              Payment successful!
            </h2>
            <p className="text-[#666666] mb-6">
              Your credits have been added to your account.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-pill btn-primary"
              data-testid="continue-btn"
            >
              Continue to Dashboard
            </button>
          </motion.div>
        )}

        {(status === 'error' || status === 'expired' || status === 'timeout') && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <XCircle size={64} className="mx-auto mb-4 text-[#E5533C]" />
            <h2 
              className="font-heading text-2xl mb-2"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              {status === 'expired' ? 'Payment expired' : 'Payment failed'}
            </h2>
            <p className="text-[#666666] mb-6">
              {status === 'timeout' 
                ? 'Payment verification timed out. Please check your email for confirmation.'
                : 'Something went wrong. Please try again.'}
            </p>
            <button
              onClick={() => navigate('/pricing')}
              className="btn-pill btn-primary"
              data-testid="try-again-btn"
            >
              Try Again
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default PaymentSuccess;
