import React from 'react';
import { motion } from 'framer-motion';

const StepList = ({ steps, currentStep }) => {
  return (
    <div className="w-full space-y-2">
      {steps.map((step, index) => {
        const stepNumber = index + 1;
        const isActive = stepNumber === currentStep;
        const isCompleted = stepNumber < currentStep;
        
        return (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`
              relative flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300
              ${isActive 
                ? 'bg-gradient-to-r from-neon-blue/20 to-transparent border border-neon-blue/30' 
                : 'hover:bg-white/5'
              }
            `}
          >
            {/* Step Indicator Dot */}
            <div className="relative flex-shrink-0">
              <motion.div
                className={`
                  w-2.5 h-2.5 rounded-full transition-all duration-300
                  ${isActive 
                    ? 'bg-neon-blue shadow-neon' 
                    : isCompleted 
                      ? 'bg-green-500' 
                      : 'bg-gray-600'
                  }
                `}
                animate={isActive ? {
                  scale: [1, 1.3, 1],
                  boxShadow: [
                    '0 0 10px rgba(0, 212, 255, 0.5)',
                    '0 0 20px rgba(0, 212, 255, 0.8)',
                    '0 0 10px rgba(0, 212, 255, 0.5)',
                  ]
                } : {}}
                transition={{ duration: 2, repeat: Infinity }}
              />
              
              {/* Pulse Ring for Active */}
              {isActive && (
                <motion.div
                  className="absolute inset-0 rounded-full bg-neon-blue"
                  initial={{ scale: 1, opacity: 0.5 }}
                  animate={{ scale: 2.5, opacity: 0 }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
            </div>
            
            {/* Step Content */}
            <div className="flex-1 min-w-0">
              <div className={`
                text-sm font-medium truncate transition-colors duration-300
                ${isActive 
                  ? 'text-neon-blue' 
                  : isCompleted 
                    ? 'text-gray-400' 
                    : 'text-gray-500'
                }
              `}>
                {step.title}
              </div>
              
              {/* Subtitle for Active Step */}
              {isActive && step.subtitle && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="text-xs text-gray-500 mt-0.5 truncate"
                >
                  {step.subtitle}
                </motion.div>
              )}
            </div>
            
            {/* Completion Check */}
            {isCompleted && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="flex-shrink-0"
              >
                <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </motion.div>
            )}
            
            {/* Step Number for Pending */}
            {!isCompleted && !isActive && (
              <span className="flex-shrink-0 text-xs text-gray-600 font-mono">
                {stepNumber}
              </span>
            )}
          </motion.div>
        );
      })}
    </div>
  );
};

export default StepList;
