import api from './api';
import { StandardResponse } from '../types/common';
import { User, UserCreate, UserUpdate, UserLogin } from '../types/user';

export const userService = {
  // 사용자 생성
  createUser: async (userData: UserCreate): Promise<StandardResponse<User>> => {
    return api.post('/users/', userData);
  },

  // 사용자 목록 조회
  getUsers: async (): Promise<StandardResponse<User[]>> => {
    return api.get('/users/');
  },

  // 특정 사용자 조회
  getUser: async (userId: number): Promise<StandardResponse<User>> => {
    return api.get(`/users/${userId}`);
  },

  // 이메일로 사용자 조회
  getUserByEmail: async (email: string): Promise<StandardResponse<User>> => {
    return api.get(`/users/email/${email}`);
  },

  // 사용자 정보 수정
  updateUser: async (userId: number, userData: UserUpdate): Promise<StandardResponse<User>> => {
    return api.put(`/users/${userId}`, userData);
  },

  // 사용자 삭제
  deleteUser: async (userId: number): Promise<StandardResponse<null>> => {
    return api.delete(`/users/${userId}`);
  },

  // 로그인
  login: async (credentials: UserLogin): Promise<StandardResponse<{ access_token: string }>> => {
    return api.post('/users/login', credentials);
  },

  // 대량 사용자 업로드
  bulkUploadUsers: async (file: File): Promise<StandardResponse<{ success: number; failed: number }>> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/users/bulk-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
}; 