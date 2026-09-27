'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  User,
  Shield,
  FileText,
  UploadCloud,
  Save,
  X,
  File,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Calendar,
  DollarSign,
  MapPin,
  AlertTriangle,
  Search,
  Loader2
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';
import { InsuranceCategory, ClaimPriority, ClaimDocument, Customer, Policy } from '@/types/insurance';
import { searchCustomers, searchPolicies, uploadDocument, verifyPolicy, uploadKnowledgeDocument } from '@/lib/api';


export default function NewClaimPage() {
  const router = useRouter();
  const { addClaim } = useClaims();

  // Customer Lookup State
  const [customerSearchQuery, setCustomerSearchQuery] = useState('');
  const [isSearchingCustomer, setIsSearchingCustomer] = useState(false);
  const [foundCustomers, setFoundCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerNotFound, setCustomerNotFound] = useState(false);

  // Customer Fields (read-only or populated from lookup)
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerDob, setCustomerDob] = useState('');
  const [customerAddress, setCustomerAddress] = useState('');
  const [nationalId, setNationalId] = useState('');

  // Policy Lookup & Verification State
  const [availablePolicies, setAvailablePolicies] = useState<Policy[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [policyNumber, setPolicyNumber] = useState('');
  const [category, setCategory] = useState<InsuranceCategory>('Vehicle');
  const [policyStart, setPolicyStart] = useState('');
  const [policyEnd, setPolicyEnd] = useState('');
  const [premiumStatus, setPremiumStatus] = useState<'Paid' | 'Pending' | 'Grace Period' | 'Overdue'>('Paid');
  const [coverageLimit, setCoverageLimit] = useState('');
  const [deductible, setDeductible] = useState('');

  // Policy Verification Result State
  const [isVerifyingPolicy, setIsVerifyingPolicy] = useState(false);
  const [policyVerification, setPolicyVerification] = useState<any | null>(null);
  const [policyDocUploading, setPolicyDocUploading] = useState(false);
  const [policyDocSuccess, setPolicyDocSuccess] = useState<string | null>(null);


  // Claim Form Details (Officer Input)
  const [claimTitle, setClaimTitle] = useState('');
  const [claimDescription, setClaimDescription] = useState('');
  const [incidentDate, setIncidentDate] = useState('');
  const [incidentTime, setIncidentTime] = useState('');
  const [claimAmount, setClaimAmount] = useState('');
  const [currency, setCurrency] = useState<'INR' | 'USD' | 'EUR' | 'GBP'>('INR');
  const [location, setLocation] = useState('');
  const [priority, setPriority] = useState<ClaimPriority>('Medium');
  const [isEmergency, setIsEmergency] = useState(false);


  // Form Submission & Validation States
  const [uploadedDocs, setUploadedDocs] = useState<ClaimDocument[]>([]);
  const [rawFiles, setRawFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Handle Customer Search
  const handleCustomerSearch = async () => {
    if (!customerSearchQuery.trim()) return;
    setIsSearchingCustomer(true);
    setCustomerNotFound(false);
    setSelectedCustomer(null);
    setFoundCustomers([]);

    try {
      const results = await searchCustomers(customerSearchQuery);
      if (results.length === 0) {
        setCustomerNotFound(true);
      } else {
        setFoundCustomers(results);
      }
    } catch (err) {
      console.error('Customer search error:', err);
      setCustomerNotFound(true);
    } finally {
      setIsSearchingCustomer(false);
    }
  };

  // Select a Customer from lookup
  const handleSelectCustomer = async (cust: Customer) => {
    setSelectedCustomer(cust);
    setCustomerName(cust.name);
    setCustomerEmail(cust.email);
    setCustomerPhone(cust.phone);
    setCustomerDob(cust.dob);
    setCustomerAddress(cust.address);
    setNationalId(cust.nationalId);
    setFoundCustomers([]);

    // Auto-fetch policy for customer
    try {
      const policies = await searchPolicies({ customer_id: cust.id });
      setAvailablePolicies(policies);
      if (policies.length > 0) {
        handleSelectPolicy(policies[0]);
      }
    } catch (pErr) {
      console.warn('Policy lookup warning:', pErr);
    }
  };

  // Select Policy
  const handleSelectPolicy = (pol: Policy) => {
    setSelectedPolicy(pol);
    setPolicyNumber(pol.policyNumber);
    setCategory(pol.category as InsuranceCategory);
    setPolicyStart(pol.startDate);
    setPolicyEnd(pol.endDate);
    setPremiumStatus(pol.premiumStatus);
    setCoverageLimit(String(pol.coverageLimit));
    setDeductible(String(pol.deductible));
    handleVerifyPolicy(pol.policyNumber);
  };

  // Perform Policy Verification Lookup in PostgreSQL
  const handleVerifyPolicy = async (polNumToVerify?: string) => {
    const targetPolNum = polNumToVerify || policyNumber;
    if (!targetPolNum.trim()) return;

    setIsVerifyingPolicy(true);
    setPolicyVerification(null);
    setPolicyDocSuccess(null);

    try {
      const result = await verifyPolicy(targetPolNum, incidentDate || undefined);
      setPolicyVerification(result);

      if (result.policyExists) {
        if (result.category) setCategory(result.category as InsuranceCategory);
        if (result.startDate) setPolicyStart(result.startDate);
        if (result.endDate) setPolicyEnd(result.endDate);
        if (result.premiumStatus) setPremiumStatus(result.premiumStatus as any);
        if (result.coverageLimit) setCoverageLimit(String(result.coverageLimit));
        if (result.deductible) setDeductible(String(result.deductible));
        if (result.currency) setCurrency(result.currency as any);

        if (result.customerName && !customerName) {
          setCustomerName(result.customerName);
          if (result.customerEmail) setCustomerEmail(result.customerEmail);
          if (result.customerPhone) setCustomerPhone(result.customerPhone);
        }
      }
    } catch (err: any) {
      console.error('Policy verification error:', err);
      setPolicyVerification({
        status: 'policy_not_found',
        policyNumber: targetPolNum,
        policyExists: false,
        isActive: false,
        isExpired: false,
        policyDocumentAvailable: false,
        issues: [`Policy verification failed: ${err.message || 'Server error'}`],
        warnings: ['Unable to verify policy record against PostgreSQL database.']
      });
    } finally {
      setIsVerifyingPolicy(false);
    }
  };

  // Upload Policy Document (PDF) if policy document is unavailable
  const handlePolicyDocUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !policyNumber.trim()) return;

    const file = files[0];
    setPolicyDocUploading(true);
    setPolicyDocSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', `${policyNumber} Customer Policy Document`);
      formData.append('document_type', 'policy');
      formData.append('policy_number', policyNumber);

      await uploadKnowledgeDocument(formData);
      setPolicyDocSuccess(`Successfully uploaded policy document '${file.name}' for policy ${policyNumber}!`);
      // Re-trigger verification
      await handleVerifyPolicy();
    } catch (err: any) {
      console.error('Policy doc upload error:', err);
      alert(`Failed to upload policy document: ${err.message}`);
    } finally {
      setPolicyDocUploading(false);
    }
  };


  // Document Upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setIsUploading(true);

    const file = files[0];
    const isImage = file.name.match(/\.(jpg|jpeg|png|webp)$/i);
    const newDoc: ClaimDocument = {
      id: `doc-${Date.now()}`,
      fileName: file.name,
      fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      type: isImage ? 'IMAGE' : file.name.endsWith('.pdf') ? 'PDF' : 'WORD',
      category: isImage ? 'Damage Photo' : 'Police Report',
      uploadDate: new Date().toISOString(),
      url: '#',
      ocrStatus: 'Pending',
      verificationStatus: 'Pending',
      ocrFields: []
    };

    setUploadedDocs((prev) => [...prev, newDoc]);
    setRawFiles((prev) => [...prev, file]);
    setIsUploading(false);
  };

  const removeDoc = (id: string) => {
    const idx = uploadedDocs.findIndex((d) => d.id === id);
    if (idx !== -1) {
      setUploadedDocs((prev) => prev.filter((_, i) => i !== idx));
      setRawFiles((prev) => prev.filter((_, i) => i !== idx));
    }
  };

  // Validate and Submit Claim
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationErrors([]);
    setApiError(null);

    const errors: string[] = [];
    if (!selectedCustomer && !customerName.trim()) errors.push('Please specify customer name or select a customer using Customer Lookup.');
    if (!selectedPolicy && !policyNumber.trim()) errors.push('Please select or specify a valid policy number.');
    if (!claimTitle.trim()) errors.push('Claim title is required.');
    if (!claimDescription.trim() || claimDescription.length < 5) errors.push('Description must be at least 5 characters long.');
    if (!incidentDate) errors.push('Incident date is required.');
    if (!location.trim()) errors.push('Incident location is required.');
    if (!claimAmount || Number(claimAmount) <= 0) errors.push('Valid claim amount is required.');

    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }

    setIsSubmitting(true);
    try {
      const newClaim = await addClaim({
        title: claimTitle,
        description: claimDescription,
        category,
        priority,
        isEmergency,
        incidentDate,
        incidentTime: incidentTime || '12:00',
        location,
        claimAmount: Number(claimAmount),
        currency,
        customer_id: selectedCustomer?.id || undefined,

        policy_number: selectedPolicy?.policyNumber || policyNumber,
        customer: selectedCustomer ? undefined : {
          name: customerName,
          email: customerEmail,
          phone: customerPhone || '+1 (555) 000-0000',
          dob: customerDob || '1990-01-01',
          address: customerAddress || 'Unspecified Address',
          nationalId: nationalId || 'SSN-000-00-0000',
          memberSince: new Date().toISOString().split('T')[0],
          riskScore: 10
        },
        policy: selectedPolicy ? undefined : {
          policyNumber: policyNumber || `POL-${category.substring(0, 3).toUpperCase()}-${Math.floor(10000 + Math.random() * 90000)}`,
          category,
          startDate: policyStart || '2026-01-01',
          endDate: policyEnd || '2027-01-01',
          premiumStatus,
          coverageLimit: Number(coverageLimit) || 50000,
          deductible: Number(deductible) || 500
        },
        documents: uploadedDocs
      });

      // Upload raw binary documents if any attached
      if (rawFiles.length > 0) {
        for (let i = 0; i < rawFiles.length; i++) {
          try {
            const docCat = uploadedDocs[i]?.category || (rawFiles[i].name.match(/\.(jpg|jpeg|png|webp)$/i) ? 'Damage Photo' : 'Police Report');
            await uploadDocument(newClaim.id, rawFiles[i], docCat);
          } catch (uploadErr) {
            console.warn(`Failed to upload document ${rawFiles[i].name}:`, uploadErr);
          }
        }
      }

      setSuccessMsg(`Claim ${newClaim.claimNumber || newClaim.id} registered successfully!`);
      setTimeout(() => {
        router.push(`/claims/${newClaim.id}`);
      }, 1200);
    } catch (err: any) {
      console.error('Error creating claim:', err);
      setApiError(err.message || 'Failed to submit claim to server. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-400" />
            New Insurance Claim Intake
          </h1>
          <p className="text-sm text-slate-400">
            Register a live claim by searching backend records or entering real intake parameters.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Validation & API Error Banners */}
      {validationErrors.length > 0 && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-1 text-sm">
          <div className="flex items-center gap-2 font-semibold">
            <AlertCircle className="w-4 h-4 text-rose-400" /> Form Validation Issues:
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-xs text-rose-200">
            {validationErrors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {apiError && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span>{apiError}</span>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center gap-2 text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* SECTION 1: Customer Search & Information */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <User className="w-5 h-5 text-indigo-400" /> 1. Customer Information
            </h2>
            {selectedCustomer && (
              <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Customer Verified
              </span>
            )}
          </div>

          {/* Customer Search Lookup */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Search Customer Database
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="Enter Customer Name, Email, or Customer ID (e.g., Alexander Vance)..."
                  value={customerSearchQuery}
                  onChange={(e) => setCustomerSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleCustomerSearch())}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <button
                type="button"
                onClick={handleCustomerSearch}
                disabled={isSearchingCustomer}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
              >
                {isSearchingCustomer ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Lookup
              </button>
            </div>
          </div>

          {/* Customer Search Results List */}
          {foundCustomers.length > 0 && (
            <div className="bg-slate-950 border border-indigo-500/30 rounded-lg p-3 space-y-2">
              <p className="text-xs text-indigo-300 font-medium">Matching Customers Found in Database:</p>
              <div className="space-y-1">
                {foundCustomers.map((cust) => (
                  <div
                    key={cust.id}
                    onClick={() => handleSelectCustomer(cust)}
                    className="p-2.5 rounded-md bg-slate-900 hover:bg-indigo-950/40 border border-slate-800 cursor-pointer flex items-center justify-between text-xs transition-colors"
                  >
                    <div>
                      <span className="font-semibold text-white">{cust.name}</span>
                      <span className="text-slate-400 ml-2">({cust.email})</span>
                    </div>
                    <span className="text-indigo-400 font-mono">ID: {cust.id}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {customerNotFound && (
            <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-300 text-xs">
              No matching customer found in database. Enter customer information manually or refine search.
            </div>
          )}

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Full Name *</label>
              <input
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="e.g. Jane Doe"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Email Address *</label>
              <input
                type="email"
                value={customerEmail}
                onChange={(e) => setCustomerEmail(e.target.value)}
                placeholder="jane.doe@example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Phone Number</label>
              <input
                type="text"
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                placeholder="+1 (555) 000-0000"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">National ID / SSN</label>
              <input
                type="text"
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
                placeholder="SSN-XXX-XX-0000"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-slate-400 block mb-1">Residential Address</label>
              <input
                type="text"
                value={customerAddress}
                onChange={(e) => setCustomerAddress(e.target.value)}
                placeholder="Street Address, City, State ZIP"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* SECTION 2: Policy Information & Verification */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-400" /> 2. Policy Verification & Details
            </h2>
            {policyVerification && (
              <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                policyVerification.status === 'policy_found'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : policyVerification.status === 'policy_document_unavailable'
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : policyVerification.status === 'policy_expired'
                  ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}>
                {policyVerification.status.toUpperCase().replace(/_/g, ' ')}
              </span>
            )}
          </div>

          {/* Policy Search / Input Row with Verification Button */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
              Enter & Verify Policy Number in PostgreSQL
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Shield className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="Enter Policy Number (e.g., POL-AUTO-99824 or POL-VEH-39102)..."
                  value={policyNumber}
                  onChange={(e) => setPolicyNumber(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleVerifyPolicy())}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
              <button
                type="button"
                onClick={() => handleVerifyPolicy()}
                disabled={isVerifyingPolicy || !policyNumber.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg flex items-center gap-2 transition-colors shrink-0"
              >
                {isVerifyingPolicy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Verify Policy
              </button>
            </div>
          </div>

          {/* Available Customer Policies Quick Picker */}
          {availablePolicies.length > 0 && (
            <div className="space-y-2 pt-1">
              <label className="text-xs text-slate-400">Or Select Customer Policy from Database:</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {availablePolicies.map((pol) => (
                  <div
                    key={pol.policyNumber}
                    onClick={() => handleSelectPolicy(pol)}
                    className={`p-3 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
                      policyNumber === pol.policyNumber
                        ? 'border-indigo-500 bg-indigo-950/40 text-white'
                        : 'border-slate-800 bg-slate-950 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="font-semibold text-white">{pol.policyNumber}</div>
                      <div className="text-slate-400">{pol.category} Insurance ({pol.startDate} to {pol.endDate})</div>
                    </div>
                    <div className="text-right">
                      <div className="text-emerald-400 font-mono">${pol.coverageLimit.toLocaleString()} Limit</div>
                      <div className="text-slate-500">{pol.premiumStatus}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Policy Verification Card Results */}
          {policyVerification && (
            <div className={`p-4 rounded-xl border text-xs space-y-2 ${
              policyVerification.status === 'policy_found'
                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
                : policyVerification.status === 'policy_document_unavailable'
                ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                : policyVerification.status === 'policy_expired'
                ? 'bg-orange-950/20 border-orange-500/30 text-orange-200'
                : 'bg-rose-950/20 border-rose-500/30 text-rose-200'
            }`}>
              <div className="flex items-center justify-between font-semibold">
                <span className="flex items-center gap-1.5">
                  {policyVerification.policyExists ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-rose-400" />}
                  Policy Verification Result: {policyVerification.policyNumber}
                </span>
                <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                  {policyVerification.status}
                </span>
              </div>

              {policyVerification.policyExists && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-1 border-t border-slate-800/60 text-[11px]">
                  <div><span className="text-slate-400 block">Category:</span> <span className="font-medium text-white">{policyVerification.category}</span></div>
                  <div><span className="text-slate-400 block">Coverage Limit:</span> <span className="font-mono text-emerald-400">{(policyVerification.currency === 'INR' || currency === 'INR') ? '₹' : '$'}{policyVerification.coverageLimit?.toLocaleString()}</span></div>
                  <div><span className="text-slate-400 block">Deductible:</span> <span className="font-mono text-slate-300">{(policyVerification.currency === 'INR' || currency === 'INR') ? '₹' : '$'}{policyVerification.deductible?.toLocaleString()}</span></div>
                  <div><span className="text-slate-400 block">Policy Period:</span> <span className="text-white">{policyVerification.startDate} to {policyVerification.endDate}</span></div>
                </div>
              )}

              {/* Warning for Missing Policy Document */}
              {policyVerification.status === 'policy_document_unavailable' && (
                <div className="p-3 bg-amber-950/40 border border-amber-500/30 rounded-lg text-amber-200 space-y-2 mt-2">
                  <div className="flex items-start gap-2 text-xs">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-amber-300">Policy Document Not Ingested in Knowledge Base</p>
                      <p className="text-[11px] text-amber-200/80">
                        The policy record exists in PostgreSQL, but its full policy terms PDF is not yet in the RAG Knowledge Base.
                        RAG analysis will mark customer policy clauses as unavailable requiring human officer verification.
                      </p>
                    </div>
                  </div>

                  {/* Optional Policy Document Ingestion UI */}
                  <div className="flex items-center gap-3 pt-1">
                    <input
                      type="file"
                      onChange={handlePolicyDocUpload}
                      accept=".pdf"
                      id="policyPdfUploadInput"
                      className="hidden"
                    />
                    <label
                      htmlFor="policyPdfUploadInput"
                      className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-md cursor-pointer flex items-center gap-1.5 transition-colors"
                    >
                      {policyDocUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UploadCloud className="w-3.5 h-3.5" />}
                      Upload Customer Policy Document (PDF)
                    </label>
                    <span className="text-[10px] text-amber-400/80">(Optional — system will proceed cleanly without overriding generic policy)</span>
                  </div>
                </div>
              )}

              {policyDocSuccess && (
                <div className="p-2 bg-emerald-500/20 border border-emerald-500/40 rounded text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  {policyDocSuccess}
                </div>
              )}

              {/* Warning / Issues List */}
              {policyVerification.issues && policyVerification.issues.length > 0 && (
                <div className="space-y-0.5 text-[11px] text-rose-300 pt-1">
                  {policyVerification.issues.map((iss: string, idx: number) => (
                    <div key={idx} className="flex items-center gap-1.5">
                      <AlertCircle className="w-3 h-3 text-rose-400" /> {iss}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Insurance Category *</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as InsuranceCategory)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="Vehicle">Vehicle Insurance</option>
                <option value="Health">Health Insurance</option>
                <option value="Home">Home Insurance</option>
                <option value="Travel">Travel Insurance</option>
                <option value="Business">Business Insurance</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">
                Coverage Limit ({currency === 'INR' ? '₹ INR' : currency === 'USD' ? '$ USD' : currency === 'EUR' ? '€ EUR' : '£ GBP'})
              </label>
              <input
                type="number"
                value={coverageLimit}
                onChange={(e) => setCoverageLimit(e.target.value)}
                placeholder="50000"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">
                Policy Deductible ({currency === 'INR' ? '₹ INR' : currency === 'USD' ? '$ USD' : currency === 'EUR' ? '€ EUR' : '£ GBP'})
              </label>
              <input
                type="number"
                value={deductible}
                onChange={(e) => setDeductible(e.target.value)}
                placeholder="500"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* SECTION 3: Claim Details (Officer Input) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="border-b border-slate-800/80 pb-3">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" /> 3. Claim Details & Incident Description
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="text-xs text-slate-400 block mb-1">Claim Title / Incident Headline *</label>
              <input
                type="text"
                value={claimTitle}
                onChange={(e) => setClaimTitle(e.target.value)}
                placeholder="e.g. Rear-end collision on Highway 101"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Claim Currency *</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white font-mono font-bold focus:outline-none focus:border-indigo-500"
              >
                <option value="INR">INR (₹ - Indian Rupee)</option>
                <option value="USD">USD ($ - US Dollar)</option>
                <option value="EUR">EUR (€ - Euro)</option>
                <option value="GBP">GBP (£ - British Pound)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">
                Claimed Amount ({currency === 'INR' ? '₹ INR' : currency === 'USD' ? '$ USD' : currency === 'EUR' ? '€ EUR' : '£ GBP'}) *
              </label>
              <div className="relative">
                <span className="w-4 h-4 absolute left-3 top-2.5 text-slate-500 font-mono text-xs font-bold">
                  {currency === 'INR' ? '₹' : currency === 'USD' ? '$' : currency === 'EUR' ? '€' : '£'}
                </span>
                <input
                  type="number"
                  value={claimAmount}
                  onChange={(e) => setClaimAmount(e.target.value)}
                  placeholder="40000"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            </div>


            <div>
              <label className="text-xs text-slate-400 block mb-1">Incident Date *</label>
              <input
                type="date"
                value={incidentDate}
                onChange={(e) => setIncidentDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Incident Location *</label>
              <div className="relative">
                <MapPin className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. 5th Ave & Main St, Cityville"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Priority Classification</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as ClaimPriority)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="Low">Low Priority</option>
                <option value="Medium">Medium Priority</option>
                <option value="High">High Priority</option>
                <option value="Emergency">Emergency Priority</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="text-xs text-slate-400 block mb-1">Incident Description & Narrative *</label>
              <textarea
                rows={4}
                value={claimDescription}
                onChange={(e) => setClaimDescription(e.target.value)}
                placeholder="Provide detailed description of the incident, damaged items, and third-party details..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="emergencyCheck"
                checked={isEmergency}
                onChange={(e) => setIsEmergency(e.target.checked)}
                className="rounded border-slate-800 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
              />
              <label htmlFor="emergencyCheck" className="text-sm text-slate-300">
                Flag for Emergency Fast-Track Escalation
              </label>
            </div>
          </div>
        </div>

        {/* SECTION 4: Document Attachments */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="border-b border-slate-800/80 pb-3">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-indigo-400" /> 4. Upload Supporting Documents
            </h2>
          </div>

          <div className="border-2 border-dashed border-slate-800 rounded-xl p-6 text-center hover:border-slate-700 transition-colors">
            <UploadCloud className="w-8 h-8 mx-auto text-slate-500 mb-2" />
            <p className="text-sm text-slate-300 font-medium">Click to select files (PDF, PNG, JPG, WEBP)</p>
            <p className="text-xs text-slate-500 mt-1">Upload police reports, damage photos, or repair estimates</p>
            <input
              type="file"
              onChange={handleFileUpload}
              className="hidden"
              id="fileUploadInput"
              accept=".pdf,.png,.jpg,.jpeg,.webp"
            />
            <label
              htmlFor="fileUploadInput"
              className="mt-3 inline-block px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg cursor-pointer transition-colors"
            >
              Browse Files
            </label>
          </div>

          {uploadedDocs.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-slate-400">Attached Documents ({uploadedDocs.length}):</p>
              <div className="space-y-2">
                {uploadedDocs.map((doc) => (
                  <div key={doc.id} className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <File className="w-4 h-4 text-indigo-400" />
                      <div>
                        <div className="font-semibold text-white">{doc.fileName}</div>
                        <div className="text-slate-400">{doc.category} • {doc.fileSize}</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeDoc(doc.id)}
                      className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Submit Actions */}
        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold flex items-center gap-2 transition-colors"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Submitting to Backend...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" /> Submit Claim Intake Record
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
