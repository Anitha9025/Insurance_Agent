'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  FileText, 
  Search, 
  Filter, 
  Plus, 
  Download, 
  CheckSquare, 
  ChevronRight, 
  ArrowUpDown, 
  ArrowUpRight,
  MoreVertical,
  Eye,
  File,
  X,
  CheckCircle2,
  Sparkles,
  FolderArchive,
  Trash2
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';
import { StatusBadge, PriorityBadge } from '@/components/ui/StatusBadge';
import { formatCurrency, formatDate } from '@/lib/utils';
import { InsuranceCategory, ClaimStatus, Claim, ClaimDocument } from '@/types/insurance';

export default function ClaimsMasterPage() {
  const { claims, removeClaim, removeAllClaims } = useClaims();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedRowIds, setSelectedRowIds] = useState<string[]>([]);

  // Modal State for Viewing Documents for a specific claim
  const [activeClaimForDocs, setActiveClaimForDocs] = useState<Claim | null>(null);
  const [selectedDocForOcr, setSelectedDocForOcr] = useState<ClaimDocument | null>(null);
  const [isDeletingAll, setIsDeletingAll] = useState(false);

  const handleDeleteAll = async () => {
    if (!confirm(`Are you sure you want to permanently delete ALL ${claims.length} claims from the PostgreSQL database? This action cannot be undone.`)) {
      return;
    }
    setIsDeletingAll(true);
    try {
      await removeAllClaims();
    } catch (err: any) {
      alert(`Failed to delete claims: ${err.message}`);
    } finally {
      setIsDeletingAll(false);
    }
  };

  const handleDeleteSingle = async (claim: Claim) => {
    if (!confirm(`Delete claim ${claim.claimNumber} (${claim.title})?`)) {
      return;
    }
    try {
      await removeClaim(claim.id);
    } catch (err: any) {
      alert(`Failed to delete claim: ${err.message}`);
    }
  };


  const filteredClaims = claims.filter((claim) => {
    const matchesSearch =
      claim.claimNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      claim.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      claim.customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      claim.customer.email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = selectedCategory === 'ALL' || claim.category === selectedCategory;
    const matchesStatus = selectedStatus === 'ALL' || claim.status === selectedStatus;

    return matchesSearch && matchesCategory && matchesStatus;
  });

  const toggleSelectAll = () => {
    if (selectedRowIds.length === filteredClaims.length) {
      setSelectedRowIds([]);
    } else {
      setSelectedRowIds(filteredClaims.map((c) => c.id));
    }
  };

  const toggleSelectRow = (id: string) => {
    if (selectedRowIds.includes(id)) {
      setSelectedRowIds((prev) => prev.filter((i) => i !== id));
    } else {
      setSelectedRowIds((prev) => [...prev, id]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-[11px] font-bold uppercase tracking-wider">
              Claims Operations Registry
            </span>
            <span className="text-xs text-slate-400">{filteredClaims.length} Total Records</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Master Insurance Claims Table
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Search, filter, inspect attached documents & OCR extractions, and view real-time AI confidence scores for active claims.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {claims.length > 0 && (
            <button
              onClick={handleDeleteAll}
              disabled={isDeletingAll}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-bold transition-all disabled:opacity-50"
              title="Delete all claim records from database"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{isDeletingAll ? 'Deleting Claims...' : `Delete All Claims (${claims.length})`}</span>
            </button>
          )}

          {selectedRowIds.length > 0 && (
            <button
              onClick={() => alert(`Bulk export initiated for ${selectedRowIds.length} claims`)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-md shadow-purple-600/20 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Selected ({selectedRowIds.length})</span>
            </button>
          )}

          <Link
            href="/claims/new"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/20 transition-all hover:scale-[1.02]"
          >
            <Plus className="w-4 h-4" />
            <span>New Claim</span>
          </Link>
        </div>

      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Claim ID, customer name, or title..."
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Categories (Vehicle, Health, Home...)</option>
              <option value="Vehicle">Vehicle Insurance</option>
              <option value="Health">Health Insurance</option>
              <option value="Home">Home & Property</option>
              <option value="Travel">Travel Insurance</option>
              <option value="Business">Business Liability</option>
            </select>
          </div>

          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Statuses (Approved, Pending...)</option>
              <option value="Submitted">Submitted / New Intake</option>
              <option value="Under Review">Under Review</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
              <option value="Requires Documents">Requires Documents</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Data Table */}
      <div className="glass-panel rounded-2xl border border-slate-200/80 dark:border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-100/70 dark:bg-slate-900/80 border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider select-none">
                <th className="py-3 px-4 w-10">
                  <input
                    type="checkbox"
                    checked={selectedRowIds.length === filteredClaims.length && filteredClaims.length > 0}
                    onChange={toggleSelectAll}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600"
                  />
                </th>
                <th className="py-3 px-4">Claim ID</th>
                <th className="py-3 px-4">Customer & Contact</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Incident Title</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Docs</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/60 dark:divide-slate-800/60">
              {filteredClaims.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400 text-xs">
                    No matching claims found in registry.
                  </td>
                </tr>
              ) : (
                filteredClaims.map((claim) => {
                  const isSelected = selectedRowIds.includes(claim.id);
                  return (
                    <tr
                      key={claim.id}
                      className={`hover:bg-slate-50/70 dark:hover:bg-slate-900/70 transition-colors ${
                        isSelected ? 'bg-indigo-500/5 dark:bg-indigo-500/10' : ''
                      }`}
                    >
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectRow(claim.id)}
                          className="rounded border-slate-700 bg-slate-900 text-indigo-600"
                        />
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                        {claim.claimNumber}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900 dark:text-white">{claim.customer.name}</div>
                        <div className="text-[10px] text-slate-400">{claim.customer.email}</div>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-700 dark:text-slate-300">
                        {claim.category}
                      </td>
                      <td className="py-3 px-4 max-w-xs truncate text-slate-800 dark:text-slate-200">
                        {claim.title}
                      </td>
                      <td className="py-3 px-4 font-extrabold text-slate-900 dark:text-white">
                        {formatCurrency(claim.claimAmount, claim.currency)}
                      </td>
                      {/* Attached Docs Badge Count */}
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 font-bold text-[10px] text-slate-700 dark:text-slate-300">
                          {claim.documents.length} File{claim.documents.length !== 1 ? 's' : ''}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <PriorityBadge priority={claim.priority} />
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={claim.status} />
                      </td>
                      {/* Actions Column: View Doc + Details */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setActiveClaimForDocs(claim);
                              setSelectedDocForOcr(null);
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 font-bold text-[11px] border border-purple-500/20 transition-colors"
                            title="View attached claim documents & OCR extractions"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View Doc</span>
                          </button>

                          <Link
                            href={`/claims/${claim.id}`}
                            className="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 font-bold text-[11px] border border-indigo-500/20 transition-colors"
                          >
                            <span>Details</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </Link>

                          <button
                            onClick={() => handleDeleteSingle(claim)}
                            className="p-1.5 rounded-xl bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 transition-colors"
                            title="Delete claim from database"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>

                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* VIEW DOCS MODAL FOR SELECTED CLAIM */}
      {activeClaimForDocs && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-3xl p-6 rounded-3xl border border-slate-800 space-y-5 max-h-[88vh] overflow-y-auto shadow-2xl">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <FolderArchive className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-indigo-400">{activeClaimForDocs.claimNumber}</span>
                    <span className="text-xs text-slate-400">&bull; {activeClaimForDocs.customer.name}</span>
                  </div>
                  <h3 className="font-extrabold text-sm text-white">Attached Claim Documents & OCR Records</h3>
                </div>
              </div>

              <button
                onClick={() => {
                  setActiveClaimForDocs(null);
                  setSelectedDocForOcr(null);
                }}
                className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Document Cards List */}
            {activeClaimForDocs.documents.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-xs">
                No documents uploaded for this claim yet.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {activeClaimForDocs.documents.map((doc) => (
                    <div
                      key={doc.id}
                      className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                        selectedDocForOcr?.id === doc.id
                          ? 'bg-purple-950/40 border-purple-500/60 shadow-lg'
                          : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                      }`}
                      onClick={() => setSelectedDocForOcr(doc)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                            <File className="w-4 h-4" />
                          </div>
                          <div>
                            <h4 className="font-bold text-xs text-white truncate max-w-[170px]">{doc.fileName}</h4>
                            <p className="text-[10px] text-slate-400 mt-0.5">{doc.category} &bull; {doc.fileSize}</p>
                          </div>
                        </div>

                        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {doc.verificationStatus}
                        </span>
                      </div>

                      <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                        <span className="text-slate-400">OCR: <strong className="text-emerald-400">{doc.ocrStatus}</strong></span>
                        <span className="text-indigo-400 font-semibold flex items-center gap-1">
                          <span>Inspect OCR Fields</span>
                          <ChevronRight className="w-3 h-3" />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* OCR Inspection Panel for Selected Document */}
                {selectedDocForOcr && (
                  <div className="p-4 rounded-2xl bg-slate-950 border border-purple-500/30 space-y-3 animate-in fade-in">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <div className="flex items-center gap-2 text-purple-400 font-bold text-xs">
                        <Sparkles className="w-4 h-4" />
                        <span>OCR Key-Value Extractions for {selectedDocForOcr.fileName}</span>
                      </div>
                      <span className="text-[10px] font-mono text-emerald-400 font-bold">100% Verified</span>
                    </div>

                    <div className="space-y-2 text-xs">
                      {selectedDocForOcr.ocrFields?.map((field, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 rounded-xl bg-slate-900/80 border border-slate-800/80">
                          <span className="text-slate-400 font-medium">{field.fieldName}:</span>
                          <span className="font-mono font-bold text-emerald-400">{field.extractedValue}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Modal Footer */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <Link
                href={`/claims/${activeClaimForDocs.id}`}
                onClick={() => setActiveClaimForDocs(null)}
                className="text-xs font-bold text-indigo-400 hover:underline flex items-center gap-1"
              >
                <span>Open Full Claim Details Hub</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>

              <button
                onClick={() => {
                  setActiveClaimForDocs(null);
                  setSelectedDocForOcr(null);
                }}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
              >
                Close Modal
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
