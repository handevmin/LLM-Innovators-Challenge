import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'https://a-in-5308aa58f6cb.herokuapp.com';

export const startInterview = async (userProfile) => {
  try {
    const response = await axios.post(`${API_URL}/start-interview`, userProfile);
    return response.data;
  } catch (error) {
    console.error('Error starting interview:', error);
    throw error;
  }
};

export const setupInterview = async (setup) => {
  try {
    const response = await axios.post(`${API_URL}/setup-interview`, setup);
    return response.data;
  } catch (error) {
    console.error('Error setting up interview:', error);
    throw error;
  }
};

export const generateQuestion = async (userProfile, setup) => {
    try {
      const response = await axios.post(`${API_URL}/generate-question`, { user_profile: userProfile, setup });
      return response.data;
    } catch (error) {
      console.error('Error generating question:', error);
      throw error;
    }
  };
  
  export const submitAnswer = async (answer, question) => {
    try {
      const response = await axios.post(`${API_URL}/submit-answer`, { answer, question });
      return response.data;
    } catch (error) {
      console.error('Error submitting answer:', error);
      throw error;
    }
  };