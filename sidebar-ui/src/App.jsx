import React from 'react';
import Sidebar from './components/Sidebar';

function App() {
  return (
    <div className="flex min-h-screen bg-dark-900">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area (Demo) */}
      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Neon Sidebar UI Demo
            </h1>
            <p className="text-gray-500">
              React + Tailwind CSS + Framer Motion으로 구현된 사이드바 UI입니다.
            </p>
          </div>
          
          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Circular Progress Feature */}
            <div className="bg-dark-800 rounded-2xl p-6 border border-white/5">
              <div className="w-12 h-12 rounded-xl bg-neon-blue/20 flex items-center justify-center mb-4">
                <span className="text-2xl">⭕</span>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">
                원형 프로그레스 바
              </h3>
              <p className="text-gray-500 text-sm">
                SVG 기반 애니메이션으로 부드러운 진행률 표시.
                Framer Motion의 useSpring으로 자연스러운 이징 적용.
              </p>
            </div>
            
            {/* Step List Feature */}
            <div className="bg-dark-800 rounded-2xl p-6 border border-white/5">
              <div className="w-12 h-12 rounded-xl bg-neon-purple/20 flex items-center justify-center mb-4">
                <span className="text-2xl">📋</span>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">
                단계별 리스트
              </h3>
              <p className="text-gray-500 text-sm">
                현재 단계 하이라이트와 완료된 단계 체크마크.
                Staggered 애니메이션으로 순차적 등장 효과.
              </p>
            </div>
            
            {/* Neon Style Feature */}
            <div className="bg-dark-800 rounded-2xl p-6 border border-white/5">
              <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center mb-4">
                <span className="text-2xl">✨</span>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">
                네온 글로우 효과
              </h3>
              <p className="text-gray-500 text-sm">
                다크 모드 기반 네온 블루 포인트 컬러.
                SVG 필터와 CSS box-shadow로 글로우 효과 구현.
              </p>
            </div>
            
            {/* Animation Feature */}
            <div className="bg-dark-800 rounded-2xl p-6 border border-white/5">
              <div className="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center mb-4">
                <span className="text-2xl">🎬</span>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">
                Framer Motion
              </h3>
              <p className="text-gray-500 text-sm">
                숫자 카운팅, 원형 애니메이션, LED 펄스 효과 등
                모든 인터랙션에 부드러운 모션 적용.
              </p>
            </div>
          </div>
          
          {/* Code Preview */}
          <div className="mt-8 bg-dark-800 rounded-2xl p-6 border border-white/5">
            <h3 className="text-white font-semibold text-lg mb-4">
              💡 주요 기술 스택
            </h3>
            <div className="flex flex-wrap gap-2">
              {['React 18', 'Tailwind CSS', 'Framer Motion', 'Vite', 'SVG Animation'].map((tech) => (
                <span 
                  key={tech}
                  className="px-3 py-1.5 rounded-full bg-neon-blue/10 text-neon-blue text-sm border border-neon-blue/20"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
