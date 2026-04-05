import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth, API } from '../App';

const Onboarding = () => {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({
    gender: '',
    orientation: '',
    dating_app: ''
  });

  const steps = [
    {
      question: "I am a...",
      field: 'gender',
      options: [
        { value: 'man', label: 'Man' },
        { value: 'woman', label: 'Woman' },
        { value: 'non-binary', label: 'Non-binary' },
        { value: 'other', label: 'Other' }
      ]
    },
    {
      question: "Interested in...",
      field: 'orientation',
      options: [
        { value: 'men', label: 'Men' },
        { value: 'women', label: 'Women' },
        { value: 'everyone', label: 'Everyone' }
      ]
    },
    {
      question: "My main dating app is...",
      field: 'dating_app',
      options: [
        { value: 'hinge', label: 'Hinge' },
        { value: 'tinder', label: 'Tinder' },
        { value: 'bumble', label: 'Bumble' },
        { value: 'other', label: 'Other' }
      ]
    }
  ];

  const handleSelect = async (value) => {
    const field = steps[step].field;
    const newData = { ...data, [field]: value };
    setData(newData);

    if (step < steps.length - 1) {
      setTimeout(() => setStep(step + 1), 300);
    } else {
      // Complete onboarding
      setLoading(true);
      try {
        await axios.post(`${API}/user/onboarding`, newData, { withCredentials: true });
        await refreshUser();
        toast.success('Profile setup complete!');
        navigate('/dashboard');
      } catch (error) {
        toast.error('Failed to save preferences');
      } finally {
        setLoading(false);
      }
    }
  };

  const currentStep = steps[step];

  return (
    <div className="app-container">
      {/* Progress */}
      <div className="px-6 pt-6">
        <div className="flex gap-2">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`flex-1 h-1 rounded-full transition-colors ${
                index <= step ? 'bg-[#C9B8E8]' : 'bg-[#E5E5E5]'
              }`}
            />
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center px-6 py-12">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <h1 
              className="font-heading text-3xl text-center mb-12"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              {currentStep.question}
            </h1>

            <div className="space-y-4">
              {currentStep.options.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleSelect(option.value)}
                  disabled={loading}
                  className={`btn-pill w-full text-lg transition-all ${
                    data[currentStep.field] === option.value
                      ? 'btn-accent'
                      : 'btn-secondary'
                  }`}
                  data-testid={`option-${option.value}`}
                >
                  {loading && data[currentStep.field] === option.value ? (
                    <div className="w-5 h-5 border-2 border-[#1A1A1A] border-t-transparent rounded-full animate-spin" />
                  ) : (
                    option.label
                  )}
                </button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Onboarding;
