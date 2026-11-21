import React, { useState } from 'react';
import {
  Brain,
  FileText,
  Plus,
  Search,
  Upload,
} from 'lucide-react';
import type { KnowledgeDocument, Memory } from '../../types';

interface MemoryViewProps {
  memories: Memory[];
  knowledgeDocs: KnowledgeDocument[];
  activeRole: string;
  onAddMemory: (memory: any) => Promise<void>;
  onSearchMemories: (q: string) => Promise<Memory[]>;
  onIngestKnowledge: (doc: any) => Promise<void>;
}

export const MemoryView: React.FC<MemoryViewProps> = ({
  memories,
  knowledgeDocs,
  activeRole,
  onAddMemory,
  onSearchMemories,
  onIngestKnowledge,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Memory[] | null>(null);
  const [searching, setSearching] = useState(false);

  // New Memory Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('preference');
  const [roleContext, setRoleContext] = useState(activeRole === 'all' ? 'personal' : activeRole);
  const [importance, setImportance] = useState(0.8);
  const [consentForTraining, setConsentForTraining] = useState(false);

  // Knowledge Ingestion
  const [showDocModal, setShowDocModal] = useState(false);
  const [docTitle, setDocTitle] = useState('');
  const [docContent, setDocContent] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const res = await onSearchMemories(searchQuery);
      setSearchResults(res);
    } finally {
      setSearching(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    await onAddMemory({
      content,
      category,
      role_context: roleContext,
      importance_score: importance,
      consent_for_training: consentForTraining,
    });

    setContent('');
    setShowAddModal(false);
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docTitle.trim() || !docContent.trim()) return;

    await onIngestKnowledge({
      title: docTitle,
      content: docContent,
      role_context: roleContext,
    });

    setDocTitle('');
    setDocContent('');
    setShowDocModal(false);
  };

  const displayMemories = searchResults !== null ? searchResults : memories;

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Personal Memory & RAG Knowledge</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Vector-indexed pgvector storage preserving your life context, preferences, and reference documents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowDocModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-semibold transition cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5 text-indigo-400" />
            <span>Ingest Document</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Memory</span>
          </button>
        </div>
      </div>

      {/* Semantic Search Bar */}
      <form onSubmit={handleSearch} className="flex items-center gap-2">
        <div className="flex-1 flex items-center gap-3 px-4 py-3 rounded-2xl bg-slate-900/80 border border-slate-800 focus-within:border-indigo-500 transition">
          <Search className="w-4 h-4 text-indigo-400 shrink-0" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your semantic memories with pgvector cosine distance..."
            className="w-full bg-transparent text-xs sm:text-sm text-slate-200 placeholder-slate-500 outline-none"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setSearchResults(null);
              }}
              className="text-xs text-slate-400 hover:text-white"
            >
              Clear
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={searching}
          className="px-5 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition cursor-pointer"
        >
          {searching ? 'Querying...' : 'Semantic Search'}
        </button>
      </form>

      {/* Main Grid: Memories + Knowledge Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Stored Memories */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Brain className="w-4 h-4 text-indigo-400" />
              <span>
                {searchResults !== null ? `Search Results (${searchResults.length})` : `Persistent Context (${memories.length})`}
              </span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">pgvector cosine distance indexing</span>
          </div>

          <div className="space-y-3">
            {displayMemories.length === 0 ? (
              <div className="text-center py-12 text-xs text-slate-400 bg-slate-900/40 rounded-3xl border border-slate-800 p-8">
                No memories found. Add preferences or chat with the AI assistant to automatically index life context.
              </div>
            ) : (
              displayMemories.map((mem) => (
                <div
                  key={mem.id}
                  className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl hover:border-slate-700 transition space-y-2 shadow-sm"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 font-bold uppercase">
                      {mem.category}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      Importance: {Math.round(mem.importance_score * 100)}% • {mem.source}
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
                    {mem.content}
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[10px] text-slate-400">
                    <span className="capitalize">Role Context: {mem.role_context}</span>
                    <span className="font-mono">{new Date(mem.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Col: Knowledge Documents (RAG) */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            <span>Ingested Documents ({knowledgeDocs.length})</span>
          </h3>

          <div className="space-y-3">
            {knowledgeDocs.length === 0 ? (
              <div className="p-6 rounded-3xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
                No documents uploaded. Ingest notes, syllabi, or project specs for RAG retrieval.
              </div>
            ) : (
              knowledgeDocs.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-1.5"
                >
                  <div className="font-semibold text-xs text-slate-200 truncate">{doc.title}</div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed font-sans">
                    {doc.content}
                  </p>
                  <div className="text-[9px] font-mono text-indigo-400">
                    Chunk #{doc.chunk_index} • {doc.role_context}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <h3 className="font-bold text-sm text-white">Add Persistent Life Memory</h3>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Context / Preference</label>
                <textarea
                  required
                  rows={3}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="e.g. I prefer doing deep work revision sessions before noon..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white capitalize"
                  >
                    <option value="preference">Preference</option>
                    <option value="responsibility">Responsibility</option>
                    <option value="goal">Goal Anchor</option>
                    <option value="decision">Important Decision</option>
                    <option value="academic">Academic Context</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Role Context</label>
                  <select
                    value={roleContext}
                    onChange={(e) => setRoleContext(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white capitalize"
                  >
                    <option value="personal">Personal</option>
                    <option value="student">Student</option>
                    <option value="professional">Professional</option>
                    <option value="entrepreneur">Entrepreneur</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2 pt-1 border-t border-slate-800">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Importance Weight</span>
                  <span className="font-mono text-indigo-400 font-bold">{importance.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={importance}
                  onChange={(e) => setImportance(parseFloat(e.target.value))}
                  className="w-full accent-indigo-500"
                />
                <label className="flex items-center gap-2 text-xs text-slate-400 pt-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={consentForTraining}
                    onChange={(e) => setConsentForTraining(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-0"
                  />
                  <span>Opt-in to local fine-tuning dataset export</span>
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
                >
                  Save Context
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Ingest Document Modal */}
      {showDocModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-lg rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <h3 className="font-bold text-sm text-white">Ingest Knowledge Text for RAG</h3>
            <form onSubmit={handleIngest} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Document Title</label>
                <input
                  required
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="e.g. Distributed Consensus Paper Notes / Startup Spec"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Document Content</label>
                <textarea
                  required
                  rows={6}
                  value={docContent}
                  onChange={(e) => setDocContent(e.target.value)}
                  placeholder="Paste article, notes, or reference documentation here..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowDocModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
                >
                  Ingest & Vectorize
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
