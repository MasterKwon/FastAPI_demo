import api from './api';
import { StandardResponse } from '../types/common';
import { Item, ItemCreate, ItemUpdate } from '../types/item';

export const itemService = {
  // 상품 생성
  createItem: async (itemData: ItemCreate, image?: File): Promise<StandardResponse<Item>> => {
    const formData = new FormData();
    Object.entries(itemData).forEach(([key, value]) => {
      formData.append(key, value);
    });
    if (image) {
      formData.append('image', image);
    }
    return api.post('/items/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // 상품 목록 조회
  getItems: async (params?: {
    name?: string;
    category?: string;
    min_price?: number;
    max_price?: number;
  }): Promise<StandardResponse<Item[]>> => {
    return api.get('/items/', { params });
  },

  // 상품 엑셀 다운로드
  downloadItemsExcel: async (): Promise<Blob> => {
    const response = await api.get('/items/download-excel', {
      responseType: 'blob',
    });
    return response.data;
  },

  // 대량 상품 업로드
  bulkUploadItems: async (file: File): Promise<StandardResponse<{ success: number; failed: number }>> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/items/bulk-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // 특정 상품 조회
  getItem: async (itemId: number): Promise<StandardResponse<Item>> => {
    return api.get(`/items/${itemId}`);
  },

  // 상품 이미지 추가
  addItemImage: async (itemId: number, image: File): Promise<StandardResponse<Item>> => {
    const formData = new FormData();
    formData.append('image', image);
    return api.post(`/items/${itemId}/image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // 상품 이미지 삭제
  deleteItemImage: async (itemId: number, imageId: number): Promise<StandardResponse<Item>> => {
    return api.delete(`/items/${itemId}/image/${imageId}`);
  },

  // 상품 정보 수정
  updateItem: async (itemId: number, itemData: ItemUpdate): Promise<StandardResponse<Item>> => {
    return api.put(`/items/${itemId}`, itemData);
  },

  // 상품 삭제
  deleteItem: async (itemId: number): Promise<StandardResponse<null>> => {
    return api.delete(`/items/${itemId}`);
  },
}; 