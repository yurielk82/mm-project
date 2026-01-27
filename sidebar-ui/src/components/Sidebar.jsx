import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import CircularProgress from './CircularProgress';
import StepList from './StepList';

const STEPS = [
  { id: 1, title: '파일 업로드', subtitle: '엑셀 파일을 업로드하세요' },
  { id: 2, title: '컬럼 설정', subtitle: '그룹화 기준을 선택하세요' },
  { id: 3, title: '데이터 검토', subtitle: '발송 대상을 확인하세요' },
  { id: 4, title: '템플릿 편집', subtitle: '이메일 내용을 작성하세요' },
  { id: 5, title: '발송', subtitle: '이메일을 발송하세요' },
];

const Sidebar = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isConnected, setIsConnected] = useState(true);
  
  const currentStepData = STEPS.find(s => s.id === currentStep);

  return (
    <motion.aside
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="w-80 h-screen bg-gradient-to-b from-dark-800 to-dark-900 border-r border-white/5 flex flex-col"
    >
      {/* ============================================
          🔝 최상단: 원형 프로그레스 + 브랜드
          ============================================ */}
      <div className="flex-shrink-0 pt-6 pb-4 px-6 border-b border-white/5">
        {/* 브랜드 로고 + 제목 (소형) */}
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-blue to-neon-purple flex items-center justify-center shadow-neon">
            <span className="text-base">📧</span>
          </div>
          <div>
            <h1 className="text-white font-bold text-base">CSO 메일머지</h1>
          </div>
        </div>
        
        {/* 원형 프로그레스 바 (상단 중앙) */}
        <div className="flex flex-col items-center">
          <CircularProgress 
            currentStep={currentStep} 
            totalSteps={STEPS.length} 
            size={160}
          />
          
          {/* 현재 단계 제목 */}
          <motion.div 
            className="mt-4 text-center"
            key={currentStep}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="text-neon-blue font-semibold text-base">
              {currentStepData?.title}
            </div>
            <div className="text-gray-500 text-xs mt-0.5">
              {currentStepData?.subtitle}
            </div>
          </motion.div>
        </div>
      </div>
      
      {/* ============================================
          📡 SMTP 연결 상태
          ============================================ */}
      <div className="px-4 py-3 border-b border-white/5">
        <motion.div 
          className={`
            flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm
            ${isConnected 
              ? 'bg-green-500/10 border border-green-500/20' 
              : 'bg-yellow-500/10 border border-yellow-500/20'
            }
          `}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <motion.div
            className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`}
            animate={{
              scale: [1, 1.3, 1],
              boxShadow: isConnected 
                ? ['0 0 5px #22c55e', '0 0 20px #22c55e', '0 0 5px #22c55e']
                : ['0 0 5px #eab308', '0 0 20px #eab308', '0 0 5px #eab308']
            }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <span className={`font-medium ${isConnected ? 'text-green-400' : 'text-yellow-400'}`}>
            {isConnected ? 'SMTP 연결됨' : 'SMTP 연결 필요'}
          </span>
        </motion.div>
      </div>
      
      {/* Step List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="text-xs text-gray-600 uppercase tracking-wider mb-3 px-4">
          전체 단계
        </div>
        <StepList steps={STEPS} currentStep={currentStep} />
      </div>
      
      {/* Demo Controls */}
      <div className="p-4 border-t border-white/5">
        <div className="text-xs text-gray-600 uppercase tracking-wider mb-3">
          Demo Controls
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
            className="flex-1 px-3 py-2 rounded-lg bg-white/5 text-gray-400 text-sm hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            ← 이전
          </button>
          <button
            onClick={() => setCurrentStep(Math.min(STEPS.length, currentStep + 1))}
            disabled={currentStep === STEPS.length}
            className="flex-1 px-3 py-2 rounded-lg bg-neon-blue/20 text-neon-blue text-sm hover:bg-neon-blue/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all border border-neon-blue/30"
          >
            다음 →
          </button>
        </div>
        <button
          onClick={() => setIsConnected(!isConnected)}
          className="w-full mt-2 px-3 py-2 rounded-lg bg-white/5 text-gray-500 text-xs hover:bg-white/10 transition-all"
        >
          SMTP 상태 토글
        </button>
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-white/5">
        <div className="text-center text-xs text-gray-600">
          <span className="text-neon-blue">v3.0.0</span> · Designed by KDH
        </div>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
