import React from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

const CircularProgress = ({ currentStep, totalSteps, size = 200 }) => {
  const progress = (currentStep / totalSteps) * 100;
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  
  // Animated progress value
  const springProgress = useSpring(progress, {
    stiffness: 60,
    damping: 15,
    mass: 1
  });
  
  const strokeDashoffset = useTransform(
    springProgress,
    [0, 100],
    [circumference, 0]
  );

  // Animated number counter
  const displayProgress = useTransform(springProgress, (value) => Math.round(value));
  
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      {/* Glow Effect Background */}
      <div 
        className="absolute inset-0 rounded-full blur-xl opacity-30"
        style={{
          background: `radial-gradient(circle, rgba(0, 212, 255, 0.4) 0%, transparent 70%)`,
        }}
      />
      
      {/* SVG Circle */}
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Background Circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="8"
        />
        
        {/* Progress Circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#neonGradient)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          style={{ strokeDashoffset }}
          filter="url(#glow)"
        />
        
        {/* Gradient Definition */}
        <defs>
          <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00d4ff" />
            <stop offset="50%" stopColor="#00a8cc" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
          
          {/* Glow Filter */}
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
      </svg>
      
      {/* Center Content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {/* Step Counter */}
        <div className="flex items-baseline gap-1">
          <motion.span 
            className="text-5xl font-bold text-white"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            {currentStep}
          </motion.span>
          <span className="text-2xl text-gray-500 font-light">/ {totalSteps}</span>
        </div>
        
        {/* Percentage */}
        <motion.div className="flex items-center gap-1 mt-2">
          <motion.span className="text-lg text-neon-blue font-medium">
            {displayProgress.get ? Math.round(springProgress.get()) : Math.round(progress)}%
          </motion.span>
          <span className="text-xs text-gray-500">완료</span>
        </motion.div>
      </div>
    </div>
  );
};

export default CircularProgress;
