import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { ChevronRight } from 'lucide-react';

const InterviewTypePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const userProfile = location.state?.userProfile || {};

  const interviewTypes = [
    {
      title: "기술 면접",
      description: "기술적 지식과 문제 해결 능력을 평가합니다.",
      image: "https://cdn.usegalileo.ai/sdxl10/624ef548-e7a6-4b12-9e29-1d248db44e1b.png",
    },
    {
      title: "인성 면접",
      description: "개인의 성격, 가치관, 팀워크 능력을 평가합니다.",
      image: "https://cdn.usegalileo.ai/sdxl10/c4cc1182-3262-43d0-9041-f45a8dfc329c.png",
    },
    {
      title: "자기소개서 기반 면접",
      description: "제출한 자기소개서를 바탕으로 질문합니다.",
      image: "https://cdn.usegalileo.ai/sdxl10/1ae134f8-c5ed-45d4-b720-87f4c201c0f1.png",
    }
  ];

  const handleSelectType = (type) => {
    navigate('/interview-atmosphere', { 
      state: { 
        userProfile,
        interviewSetup: { interview_type: type }
      } 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6 flex flex-col justify-center items-center">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="bg-blue-500 text-white py-6">
          <h1 className="text-3xl font-bold text-center">면접 유형 선택</h1>
        </div>
        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {interviewTypes.map((type, index) => (
              <Card key={index} className="flex flex-col overflow-hidden shadow-lg transition-transform duration-300 hover:scale-105">
                <img src={type.image} alt={type.title} className="w-full h-48 object-cover" />
                <CardContent className="flex-grow p-4">
                  <h2 className="text-xl font-semibold text-blue-600 mb-2">{type.title}</h2>
                  <p className="text-gray-600 text-sm">{type.description}</p>
                </CardContent>
                <CardFooter className="p-4 pt-0">
                  <Button 
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1 flex items-center justify-center"
                    onClick={() => handleSelectType(type.title)}
                  >
                    선택 <ChevronRight className="ml-2" size={16} />
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewTypePage;