import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const conversationAPI = {
  create: async (title = 'New Conversation') => {
    const response = await axios.post(
      `${API_URL}/conversations/`,
      { title },
      { headers: getAuthHeader() }
    );
    return response.data;
  },

  list: async () => {
    const response = await axios.get(`${API_URL}/conversations/`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  get: async (id) => {
    const response = await axios.get(`${API_URL}/conversations/${id}`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  delete: async (id) => {
    await axios.delete(`${API_URL}/conversations/${id}`, {
      headers: getAuthHeader()
    });
  }
};

export const chatAPI = {
  sendMessage: async (conversationId, content, inputMode = 'text') => {
    const response = await axios.post(
      `${API_URL}/chat/send?conversation_id=${conversationId}`,
      { content, input_mode: inputMode },
      { headers: getAuthHeader() }
    );
    return response.data;
  },

  getVideoStatus: async (taskId) => {
    const response = await axios.get(`${API_URL}/chat/video-status/${taskId}`, {
      headers: getAuthHeader()
    });
    return response.data;
  }
};

export const knowledgeAPI = {
  create: async (data) => {
    const response = await axios.post(
      `${API_URL}/knowledge/`,
      data,
      { headers: getAuthHeader() }
    );
    return response.data;
  },

  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(
      `${API_URL}/knowledge/upload`,
      formData,
      {
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  },

  list: async () => {
    const response = await axios.get(`${API_URL}/knowledge/`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  delete: async (id) => {
    await axios.delete(`${API_URL}/knowledge/${id}`, {
      headers: getAuthHeader()
    });
  }
};

export const avatarAPI = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(
      `${API_URL}/avatars/upload`,
      formData,
      {
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  },

  getStatus: async (avatarId) => {
    const response = await axios.get(`${API_URL}/avatars/status/${avatarId}`, {
      headers: getAuthHeader()
    });
    return response.data;
  },

  getMy: async () => {
    const response = await axios.get(`${API_URL}/avatars/my-avatar`, {
      headers: getAuthHeader()
    });
    return response.data;
  }
};

export const userAPI = {
  updateProfile: async (data) => {
    const response = await axios.put(
      `${API_URL}/users/profile`,
      data,
      { headers: getAuthHeader() }
    );
    return response.data;
  },

  getProfile: async () => {
    const response = await axios.get(`${API_URL}/users/profile`, {
      headers: getAuthHeader()
    });
    return response.data;
  }
};