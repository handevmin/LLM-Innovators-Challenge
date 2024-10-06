import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Share2, RefreshCw } from 'lucide-react';
import Layout from '@/components/Layout';

const AIFeedbackPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("analysis");

  const handleShare = () => {
    console.log("Sharing results...");
  };

  const handleRetry = () => {
    navigate('/');
  };

  return (
    <Layout title="AI 분석 및 피드백">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 h-14">
          <TabsTrigger value="analysis" className="text-lg py-3 h-12">분석</TabsTrigger>
          <TabsTrigger value="script" className="text-lg py-3 h-12">스크립트</TabsTrigger>
        </TabsList>
        <TabsContent value="analysis">
          <Card className="shadow-lg">
            <CardHeader className="bg-blue-500 text-white">
              <CardTitle className="text-2xl">면접 분석</CardTitle>
              <CardDescription className="text-blue-100">AI가 분석한 당신의 면접 결과입니다.</CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {['강점', '개선할 점', '추가사항'].map((section, index) => (
                <div key={section} className={`mb-6 ${index !== 0 ? 'border-t pt-6' : ''}`}>
                  <h3 className="font-semibold text-xl mb-3 text-blue-700">{section}</h3>
                  <ul className="list-disc pl-5 space-y-2">
                    {section === '강점' && [
                      '명확한 의사소통 능력',
                      '기술적 지식의 깊이',
                      '열정과 적극성'
                    ].map((item, i) => <li key={i} className="text-gray-700">{item}</li>)}
                    {section === '개선할 점' && [
                      '구체적인 예시 부족',
                      '시간 관리 개선 필요',
                      '비언어적 커뮤니케이션 향상'
                    ].map((item, i) => <li key={i} className="text-gray-700">{item}</li>)}
                    {section === '추가사항' && [
                      '프로젝트 경험에 대해 더 자세히 설명하면 좋을 것 같습니다.'
                    ].map((item, i) => <li key={i} className="text-gray-700">{item}</li>)}
                  </ul>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="script">
          <Card className="shadow-lg">
            <CardHeader className="bg-indigo-500 text-white">
              <CardTitle className="text-2xl">면접 스크립트</CardTitle>
              <CardDescription className="text-indigo-100">면접 대화 내용의 전체 스크립트입니다.</CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {[
                { speaker: '면접관', content: '안녕하세요. 자기소개 부탁드립니다.' },
                { speaker: '지원자', content: '안녕하세요. 저는 [이름]입니다. [간단한 자기소개]' },
                { speaker: '면접관', content: '네, 감사합니다. 프로젝트 경험에 대해 말씀해 주세요.' },
                { speaker: '지원자', content: '네, 제가 진행한 프로젝트는 [프로젝트 설명]' }
              ].map((dialogue, index) => (
                <div key={index} className="mb-4 flex items-start">
                  <div className={`font-semibold mr-3 ${dialogue.speaker === '면접관' ? 'text-indigo-600' : 'text-green-600'}`}>
                    {dialogue.speaker}:
                  </div>
                  <div className="flex-1">{dialogue.content}</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      <div className="mt-8 flex justify-center space-x-6">
        <Button onClick={handleShare} className="bg-green-500 hover:bg-green-600 text-white px-6 h-12 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1">
          <Share2 className="mr-2 h-5 w-5" /> 결과 공유
        </Button>
        <Button onClick={handleRetry} className="bg-blue-500 hover:bg-blue-600 text-white px-6 h-12 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1">
          <RefreshCw className="mr-2 h-5 w-5" /> 다시 하기
        </Button>
      </div>
    </Layout>
  );
};

export default AIFeedbackPage;