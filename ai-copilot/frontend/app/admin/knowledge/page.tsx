'use client';

import { useState, useEffect } from 'react';
import { BookOpen, Plus } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Spinner } from '@/components/ui/Spinner';
import { KnowledgeUpload } from '@/components/admin/KnowledgeUpload';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import * as knowledgeService from '@/services/knowledge';
import toast from 'react-hot-toast';
import type { Document, Collection } from '@/types/knowledge';

export default function KnowledgeManagementPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [showCreateCollection, setShowCreateCollection] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [newCollectionDesc, setNewCollectionDesc] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [docs, colls] = await Promise.all([
        knowledgeService.getDocuments(),
        knowledgeService.getCollections(),
      ]);
      setDocuments(docs.items || []);
      setCollections(colls.items || []);
    } catch {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    try {
      const doc = await knowledgeService.uploadDocument({ file, title: file.name });
      setDocuments((prev) => [doc, ...prev]);
      toast.success('Document uploaded successfully');
    } catch {
      toast.error('Failed to upload document');
    }
  };

  const handleIngestURL = async (url: string) => {
    try {
      const doc = await knowledgeService.ingestURL({ url });
      setDocuments((prev) => [doc, ...prev]);
      toast.success('URL ingested successfully');
    } catch {
      toast.error('Failed to ingest URL');
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await knowledgeService.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      toast.success('Document deleted');
    } catch {
      toast.error('Failed to delete document');
    }
  };

  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) return;
    try {
      const coll = await knowledgeService.createCollection({
        name: newCollectionName,
        description: newCollectionDesc,
      });
      setCollections((prev) => [...prev, coll]);
      setShowCreateCollection(false);
      setNewCollectionName('');
      setNewCollectionDesc('');
      toast.success('Collection created');
    } catch {
      toast.error('Failed to create collection');
    }
  };

  const statusVariant = (status: string) => {
    switch (status) {
      case 'processed':
        return 'green';
      case 'processing':
        return 'yellow';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
            Knowledge Base
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Manage documents and collections for AI-powered support
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setShowCreateCollection(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Collection
          </Button>
          <Button
            onClick={() => setShowUpload(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Upload Document
          </Button>
        </div>
      </div>

      {/* Collections */}
      {collections.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">
            Collections
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {collections.map((coll) => (
              <Card key={coll.id} hover>
                <CardContent className="py-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex items-center justify-center shrink-0">
                      <BookOpen className="w-5 h-5 text-primary-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-neutral-900 dark:text-white truncate">
                        {coll.name}
                      </p>
                      <p className="text-xs text-neutral-500 mt-0.5 truncate">
                        {coll.description || 'No description'}
                      </p>
                      <p className="text-xs text-neutral-400 mt-1">
                        {coll.document_count || 0} documents
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Documents */}
      <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">
        Documents
      </h2>
      {documents.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="w-8 h-8" />}
          title="No documents yet"
          description="Upload documents or ingest URLs to build your knowledge base."
          actionLabel="Upload Document"
          onAction={() => setShowUpload(true)}
        />
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-4 p-4 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl"
            >
              <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-700 flex items-center justify-center shrink-0">
                <BookOpen className="w-5 h-5 text-neutral-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
                  {doc.title || doc.filename || 'Untitled'}
                </p>
                <p className="text-xs text-neutral-500 mt-0.5">
                  {doc.source_type || 'file'} &middot;{' '}
                  {doc.chunk_count || 0} chunks
                </p>
              </div>
              <Badge variant={statusVariant(doc.status)}>{doc.status}</Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(doc.id)}
                className="text-error-500 hover:text-error-600"
              >
                Delete
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={showUpload}
        onClose={() => setShowUpload(false)}
        title="Upload Knowledge"
        size="lg"
      >
        <KnowledgeUpload
          documents={documents}
          onUpload={handleUpload}
          onIngestURL={handleIngestURL}
          onDelete={handleDelete}
        />
      </Modal>

      {/* Create Collection Modal */}
      <Modal
        isOpen={showCreateCollection}
        onClose={() => setShowCreateCollection(false)}
        title="Create Collection"
        actions={
          <>
            <Button variant="outline" onClick={() => setShowCreateCollection(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateCollection} disabled={!newCollectionName.trim()}>
              Create
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Name
            </label>
            <input
              type="text"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              placeholder="Collection name"
              className="w-full h-10 px-3 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 input-focus"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Description
            </label>
            <textarea
              value={newCollectionDesc}
              onChange={(e) => setNewCollectionDesc(e.target.value)}
              placeholder="Optional description"
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 input-focus resize-none"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
