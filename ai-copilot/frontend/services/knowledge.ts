import { api } from '@/lib/api';
import type { Document, Collection, CreateCollectionRequest } from '@/types/knowledge';
import type { PaginatedResponse } from '@/types';

export async function getDocuments(): Promise<PaginatedResponse<Document>> {
  return api.get<PaginatedResponse<Document>>('/api/v1/knowledge/documents');
}

export async function uploadDocument(file: File, collectionId?: string, title?: string): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);
  if (collectionId) formData.append('collection_id', collectionId);
  if (title) formData.append('title', title);
  return api.postFormData<Document>('/api/v1/knowledge/documents', formData);
}

export async function deleteDocument(id: string): Promise<void> {
  return api.delete(`/api/v1/knowledge/documents/${id}`);
}

export async function ingestURL(url: string, collectionId?: string, title?: string): Promise<Document> {
  return api.post<Document>('/api/v1/knowledge/ingest-url', {
    url,
    collection_id: collectionId,
    title,
  });
}

export async function getCollections(): Promise<PaginatedResponse<Collection>> {
  return api.get<PaginatedResponse<Collection>>('/api/v1/knowledge/collections');
}

export async function createCollection(data: CreateCollectionRequest): Promise<Collection> {
  return api.post<Collection>('/api/v1/knowledge/collections', data);
}
