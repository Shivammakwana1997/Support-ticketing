export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed';

export interface Document {
  id: string;
  title: string;
  source_type: 'file' | 'url' | 'text';
  source_url?: string;
  file_name?: string;
  file_size?: number;
  mime_type?: string;
  status: DocumentStatus;
  chunk_count: number;
  collection_id?: string;
  error_message?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeChunk {
  id: string;
  document_id: string;
  content: string;
  embedding_id?: string;
  chunk_index: number;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Collection {
  id: string;
  name: string;
  description?: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface UploadDocumentRequest {
  file: File;
  collection_id?: string;
  title?: string;
}

export interface IngestURLRequest {
  url: string;
  collection_id?: string;
  title?: string;
}

export interface CreateCollectionRequest {
  name: string;
  description?: string;
}
