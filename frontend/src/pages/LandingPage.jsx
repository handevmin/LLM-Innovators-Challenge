import React from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { ChevronRight } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  const handleStart = () => {
    navigate('/career-info');
  };

  return (
    <div className="min-h-screen bg-blue-50 p-6 flex flex-col items-center justify-center">
      <Card className="w-full max-w-3xl bg-white rounded-3xl shadow-lg overflow-hidden">
        <div className="bg-blue-500 text-white py-8 px-10">
          <h1 className="text-4xl font-bold text-center">A-in</h1>
        </div>
        <CardContent className="p-10">
          <div className="bg-blue-500 text-white p-8 rounded-2xl mb-8">
            <h2 className="text-3xl font-bold mb-3">A-in AI 인터뷰</h2>
            <p className="text-lg">IT 취업 준비생을 위한 맞춤형 면접 시뮬레이션</p>
          </div>
          
          <h3 className="text-2xl font-semibold text-blue-700 mb-6">서비스 소개</h3>
          <ul className="space-y-4 mb-8">
            {[
              "AI 기반 맞춤형 면접 연습",
              "기술면접, 인성면접, 자기소개서 기반 면접 지원",
              "실시간 AI 캐릭터와의 대화형 면접",
              "상세한 피드백과 개선점 분석",
              "다양한 면접 분위기 선택 가능"
            ].map((item, index) => (
              <li key={index} className="flex items-center text-gray-700">
                <ChevronRight className="mr-3 h-6 w-6 text-blue-500 flex-shrink-0" />
                <span className="text-lg">{item}</span>
              </li>
            ))}
          </ul>
          <Button 
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-6 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1 flex items-center justify-center text-xl"
            onClick={handleStart}
          >
            시작하기 <ChevronRight className="ml-2" size={24} />
          </Button>
        </CardContent>
      </Card>
      
      <footer className="mt-8 text-center text-gray-600 text-base">
        © 2024 A-in. All rights reserved.
      </footer>
    </div>
  );
};

export default LandingPage;