import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ChevronRight } from 'lucide-react';
import Layout from '@/components/Layout';

const TechStackPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedTechs, setSelectedTechs] = useState([]);
  const userProfile = location.state?.userProfile || {};

  const techStacks = {
    'Frontend': ['React', 'Angular', 'Vue.js', 'Next.js', 'Svelte'],
    'Backend': ['Node.js', 'Python', 'Java', 'Spring', 'Django', 'Express'],
    'Database': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis'],
    'DevOps': ['Docker', 'Kubernetes', 'Jenkins', 'GitLab CI'],
    'Cloud': ['AWS', 'Azure', 'Google Cloud'],
    'AI/ML': ['TensorFlow', 'PyTorch', 'Scikit-learn']
  };

  const handleTechChange = (tech) => {
    setSelectedTechs(prev => 
      prev.includes(tech) ? prev.filter(t => t !== tech) : [...prev, tech]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const updatedUserProfile = {
      ...userProfile,
      job_interest: selectedTechs.join(', ')
    };
    navigate('/interview-type', { state: { userProfile: updatedUserProfile } });
  };

  return (
    <Layout title="기술 스택 선택">
      <form onSubmit={handleSubmit}>
        {Object.entries(techStacks).map(([category, techs]) => (
          <div key={category} className="mb-6">
            <h2 className="text-xl font-semibold text-gray-600 mb-3">{category}</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {techs.map(tech => (
                <Button
                  key={tech}
                  type="button"
                  variant={selectedTechs.includes(tech) ? "default" : "outline"}
                  onClick={() => handleTechChange(tech)}
                  className={`w-full transition-all text-base font-bold text-gray-400 duration-200 ${
                    selectedTechs.includes(tech) 
                      ? 'bg-blue-500 hover:bg-blue-600 text-white' 
                      : 'bg-white hover:bg-blue-100'
                  }`}
                >
                  {tech}
                </Button>
              ))}
            </div>
          </div>
        ))}
        <Button 
          type="submit" 
          className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1 flex items-center justify-center mt-6"
        >
          다음 <ChevronRight className="ml-2" size={20} />
        </Button>
      </form>
    </Layout>
  );
};

export default TechStackPage;