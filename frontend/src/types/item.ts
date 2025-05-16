export interface Item {
  id: number;
  name: string;
  description?: string;
  price: number;
  tax?: number;
  created_at: string;
  images?: ItemImage[];
}

export interface ItemImage {
  id: number;
  item_id: number;
  file_path: string;
  created_at: string;
}

export interface ItemCreate {
  name: string;
  description?: string;
  price: number;
  tax?: number;
}

export interface ItemUpdate {
  name?: string;
  description?: string;
  price?: number;
  category?: string;
  stock?: number;
} 