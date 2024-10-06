import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronRight } from 'lucide-react';
import { setupInterview } from '@/utils/api';

const InterviewAtmospherePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { userProfile, interviewSetup } = location.state || {};

  const atmosphereTypes = [
    {
      title: "일반 면접",
      description: "표준적인 면접 분위기로 진행됩니다.",
      image: "https://cdn.usegalileo.ai/sdxl10/fa7690a8-e5cc-48f2-b866-dd47a6cdab3d.png",
    },
    {
      title: "압박 면접",
      description: "압박 면접 상황에서의 대처 능력을 평가합니다.",
      image: "https://cdn.usegalileo.ai/sdxl10/4207f057-7b9f-4264-9cc0-fc1358b5c0e0.png",
    },
    {
      title: "편안한 면접",
      description: "편안한 분위기에서 진행됩니다.",
      image: "https://cdn.usegalileo.ai/sdxl10/35b3a66c-9183-483d-a799-60566c1861a6.png",
    }
  ];

  const handleSelectAtmosphere = async (atmosphere) => {
    try {
      const fullSetup = {
        ...interviewSetup,
        interview_atmosphere: atmosphere,
        num_questions: 1
      };
      await setupInterview(fullSetup);
      navigate('/interview-session', { state: { userProfile, interviewSetup: fullSetup } });
    } catch (error) {
      console.error('Error setting up interview:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6 flex flex-col justify-center items-center">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="bg-blue-500 text-white py-6">
          <h1 className="text-3xl font-bold text-center">면접 분위기 선택</h1>
        </div>
        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {atmosphereTypes.map((type, index) => (
              <Card key={index} className="flex flex-col overflow-hidden shadow-lg transition-transform duration-300 hover:scale-105">
                <img src={type.image} alt={type.title} className="w-full h-48 object-cover" />
                <CardContent className="flex-grow p-4">
                  <h2 className="text-xl font-semibold text-blue-600 mb-2">{type.title}</h2>
                  <p className="text-gray-600 text-sm">{type.description}</p>
                </CardContent>
                <CardFooter className="p-4 pt-0">
                  <Button 
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1 flex items-center justify-center"
                    onClick={() => handleSelectAtmosphere(type.title)}
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

export default InterviewAtmospherePage;