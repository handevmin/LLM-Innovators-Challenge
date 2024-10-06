import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Mic, MicOff, MessageSquare, RefreshCw, VolumeX, Volume2 } from 'lucide-react';
import Layout from '@/components/Layout';
import { generateQuestion, submitAnswer } from '@/utils/api';


const removeQuotes = (str) => {
  return str.replace(/^['"]|['"]$/g, '');
};

const AIInterviewSession = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { userProfile, interviewSetup } = location.state || {};
  const [isMicOn, setIsMicOn] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [userAnswer, setUserAnswer] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [questionCount, setQuestionCount] = useState(0);
  const totalQuestions = 1;
  const [questionQueue, setQuestionQueue] = useState([]);
  const [isInterviewComplete, setIsInterviewComplete] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  const speechSynthesis = window.speechSynthesis;
  const [isRecognitionActive, setIsRecognitionActive] = useState(false);
  const speechRecognition = useRef(null);

  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      speechRecognition.current = new SpeechRecognition();
      speechRecognition.current.continuous = true;
      speechRecognition.current.interimResults = true;
      speechRecognition.current.lang = 'ko-KR';

      speechRecognition.current.onstart = () => {
        console.log('Speech recognition started');
        setIsRecognitionActive(true);
        setIsMicOn(true);
      };

      speechRecognition.current.onend = () => {
        console.log('Speech recognition ended');
        setIsRecognitionActive(false);
        setIsMicOn(false);
        setInterimTranscript('');
      };

      speechRecognition.current.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        setError('음성 인식 중 오류가 발생했습니다.');
        setIsRecognitionActive(false);
        setIsMicOn(false);
      };

      speechRecognition.current.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        console.log('Interim transcript:', interimTranscript);
        console.log('Final transcript:', finalTranscript);

        setInterimTranscript(interimTranscript);
        if (finalTranscript) {
          setUserAnswer(prev => prev + ' ' + finalTranscript);
        }
      };
    } else {
      console.error('Speech recognition not supported');
      setError('이 브라우저는 음성 인식을 지원하지 않습니다.');
    }

    return () => {
      if (speechRecognition.current) {
        speechRecognition.current.abort();
      }
    };
  }, []);

  const speakQuestion = (text) => {
    if (speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ko-KR';
      speechSynthesis.speak(utterance);
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }
  };


  const getNextQuestion = useCallback(async () => {
    if (questionCount >= totalQuestions || isInterviewComplete) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await generateQuestion(userProfile, interviewSetup);
      if (response && response.질문) {
        const cleanedQuestion = removeQuotes(response.질문);
        setQuestionQueue(prev => [...prev, cleanedQuestion]);
      } else {
        throw new Error("질문을 생성하지 못했습니다.");
      }
    } catch (error) {
      console.error('Error generating question:', error);
      setError("질문 생성에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  }, [userProfile, interviewSetup, questionCount, totalQuestions, isInterviewComplete]);

  useEffect(() => {
    if (questionQueue.length === 0 && questionCount < totalQuestions && !isInterviewComplete) {
      getNextQuestion();
    } else if (questionQueue.length > 0 && !currentQuestion && !isInterviewComplete) {
      const nextQuestion = questionQueue[0];
      setCurrentQuestion(nextQuestion);
      setConversation(prev => [...prev, { speaker: "AI", message: nextQuestion }]);
      setQuestionQueue(prev => prev.slice(1));
      setQuestionCount(prev => prev + 1);
      speakQuestion(nextQuestion);
    }
  }, [questionQueue, currentQuestion, questionCount, totalQuestions, getNextQuestion, isInterviewComplete]);

  const handleSubmitAnswer = async () => {
    if (!userAnswer || isInterviewComplete) return;

    setConversation(prev => [...prev, { speaker: "사용자", message: userAnswer }]);
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await submitAnswer(userAnswer, currentQuestion);
      if (response && response.피드백) {
        const cleanedFeedback = removeQuotes(response.피드백);
        setConversation(prev => [...prev, { speaker: "AI", message: cleanedFeedback }]);
        setUserAnswer('');
        setCurrentQuestion('');
        if (questionCount >= totalQuestions) {
          setIsInterviewComplete(true);
          setConversation(prev => [...prev, { speaker: "AI", message: "면접이 종료되었습니다. 피드백을 확인해 주세요." }]);
        }
      } else {
        throw new Error("피드백을 생성하지 못했습니다.");
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
      setError("답변 제출에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMic = () => {
    if (isRecognitionActive) {
      speechRecognition.current.stop();
    } else {
      try {
        setInterimTranscript('');
        speechRecognition.current.start();
      } catch (error) {
        console.error('Error starting speech recognition:', error);
        setError('음성 인식을 시작하는 데 문제가 발생했습니다.');
      }
    }
  };

  const handleFeedback = () => {
    navigate('/feedback', { state: { conversation } });
  };

  return (
    <Layout title="AI 면접 세션">
      <div className="flex flex-col items-center space-y-6">
        <div className="w-32 h-32 bg-white rounded-full overflow-hidden shadow-lg">
          <img 
            src="https://cdn.usegalileo.ai/sdxl10/3e399f07-218b-4019-9de7-0ffe32f84f67.png" 
            alt="AI Interviewer" 
            className="w-full h-full object-cover"
          />
        </div>
        <Card className="w-full shadow-lg">
          <CardContent className="p-4">
            <div className="mb-4 text-center">
              <span className="font-bold">질문 1/1</span>
            </div>
            <div className="h-64 overflow-y-auto bg-white rounded-lg p-4">
              {conversation.map((entry, index) => (
                <div key={index} className={`mb-4 flex ${entry.speaker === "AI" ? "justify-start" : "justify-end"}`}>
                  <span className={`inline-block px-4 py-2 rounded-lg max-w-[70%] ${
                    entry.speaker === "AI" 
                      ? "bg-blue-100 text-blue-800" 
                      : "bg-green-100 text-green-800"
                  }`}>
                    {entry.message}
                  </span>
                </div>
              ))}
              {isLoading && (
                <div className="text-center text-gray-500">
                  <RefreshCw className="animate-spin inline-block mr-2" />
                  처리 중...
                </div>
              )}
              {error && (
                <div className="text-center text-red-500">
                  {error}
                </div>
              )}
            </div>
            <textarea
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="답변을 입력하세요"
              className="w-full mt-4 p-2 border rounded"
              disabled={isLoading || isInterviewComplete}
            />
            {isMicOn && interimTranscript && (
              <div className="mt-2 p-2 bg-gray-100 rounded">
                음성 인식 중: {interimTranscript}
              </div>
            )}
            <Button 
              onClick={handleSubmitAnswer} 
              className="mt-2" 
              disabled={isLoading || !userAnswer || isInterviewComplete}
            >
              답변 제출
            </Button>
          </CardContent>
        </Card>
<div className="flex justify-center space-x-6">
          <Button 
            onClick={toggleMic} 
            className={`rounded-full w-16 h-16 flex items-center justify-center shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1 ${
              isMicOn ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
            }`}
            disabled={isLoading || isInterviewComplete}
          >
            {isMicOn ? <MicOff size={28} /> : <Mic size={28} />}
          </Button>
          <Button 
            onClick={toggleMute} 
            className={`rounded-full w-16 h-16 flex items-center justify-center shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1 ${
              isMuted ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            {isMuted ? <VolumeX size={28} /> : <Volume2 size={28} />}
          </Button>
          <Button 
            onClick={handleFeedback} 
            className="bg-blue-500 hover:bg-blue-600 px-6 h-16 text-lg flex items-center justify-center space-x-3 rounded-full shadow-md transition duration-300 ease-in-out transform hover:-translate-y-1"
            disabled={!isInterviewComplete || isLoading}
          >
            <MessageSquare size={28} />
            <span>피드백 보러가기</span>
          </Button>
        </div>
      </div>
    </Layout>
  );
};

export default AIInterviewSession;