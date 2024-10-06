import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ChevronRight } from 'lucide-react';
import FileUpload from '@/components/FileUpload';
import Layout from '@/components/Layout';
import { startInterview } from '@/utils/api';

const CareerInfoPage = () => {
  const navigate = useNavigate();
  const [targetCompany, setTargetCompany] = useState('');
  const [careerHistory, setCareerHistory] = useState('');
  const [resumeFile, setResumeFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const userProfile = {
        profile: careerHistory,
        company_name: targetCompany,
        job_interest: "To be filled in next page" // TechStackPage에서 업데이트
      };
      await startInterview(userProfile);
      navigate('/tech-stack', { state: { userProfile } });
    } catch (error) {
      console.error('Error starting interview:', error);
    }
  };

  const handleFileUpload = (file) => {
    setResumeFile(file);
  };

  return (
    <Layout title="목표 기업 및 경력사항 입력">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="targetCompany" className="block text-lg font-bold text-gray-500 mb-1">
            목표기업
          </label>
          <Input
            id="targetCompany"
            value={targetCompany}
            onChange={(e) => setTargetCompany(e.target.value)}
            placeholder="지원하고자 하는 기업명을 입력하세요"
            className="w-full p-2 border rounded-md"
            required
          />
        </div>
        <div>
          <label htmlFor="careerHistory" className="block text-lg font-bold text-gray-500 mb-1">
            경력사항
          </label>
          <Textarea
            id="careerHistory"
            value={careerHistory}
            onChange={(e) => setCareerHistory(e.target.value)}
            placeholder="관련 경력사항을 입력하세요. 신입의 경우 프로젝트 경험 등을 작성해 주세요."
            rows={5}
            className="w-full p-2 border rounded-md"
            required
          />
        </div>
        <FileUpload onFileUpload={handleFileUpload} />
        <Button 
          type="submit" 
          className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1 flex items-center justify-center"
        >
          다음 <ChevronRight className="ml-2" size={20} />
        </Button>
      </form>
    </Layout>
  );
};

export default CareerInfoPage;