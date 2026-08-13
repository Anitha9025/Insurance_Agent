'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  User, 
  Shield, 
  FileText, 
  UploadCloud, 
  Sparkles, 
  Save, 
  X, 
  File, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Trash2,
  Calendar,
  DollarSign,
  MapPin,
  AlertTriangle,
  Eye
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';
import { InsuranceCategory, ClaimPriority, ClaimDocument } from '@/types/insurance';

export default function NewClaimPage() {
  const router = useRouter();
  const { addClaim, setIsProcessing, setCurrentProcessingStep } = useClaims();

  // Form State
  const [customerName, setCustomerName] = useState('Alexander Vance');
  const [customerEmail, setCustomerEmail] = useState('alex.vance@enterprise.com');
  const [customerPhone, setCustomerPhone] = useState('+1 (555) 234-5678');
  const [customerDob, setCustomerDob] = useState('1984-11-14');
  const [customerAddress, setCustomerAddress] = useState('742 Evergreen Terrace, Springfield, PA 19064');
  const [nationalId, setNationalId] = useState('SSN-XXX-XX-4891');

  const [policyNumber, setPolicyNumber] = useState('POL-AUTO-99824');
  const [category, setCategory] = useState<InsuranceCategory>('Vehicle');
  const [policyStart, setPolicyStart] = useState('2025-05-01');
  const [policyEnd, setPolicyEnd] = useState('2027-05-01');
  const [premiumStatus, setPremiumStatus] = useState<'Paid' | 'Pending' | 'Grace Period' | 'Overdue'>('Paid');
  const [coverageLimit, setCoverageLimit] = useState('50000');
  const [deductible, setDeductible] = useState('500');

  const [claimTitle, setClaimTitle] = useState('Multi-vehicle collision on Interstate 95 highway');
  const [claimDescription, setClaimDescription] = useState('Vehicle sustained heavy front bumper, hood, and radiator damage following a 3-car pileup during heavy rainfall. Third-party liability involved.');
  const [incidentDate, setIncidentDate] = useState('2026-08-01');
  const [incidentTime, setIncidentTime] = useState('14:30');
  const [claimAmount, setClaimAmount] = useState('18450');
  const [location, setLocation] = useState('I-95 Exit 42, Philadelphia, PA');
  const [priority, setPriority] = useState<ClaimPriority>('Emergency');
  const [isEmergency, setIsEmergency] = useState(true);

  // Document Upload State
  const [uploadedDocs, setUploadedDocs] = useState<ClaimDocument[]>([
    {
      id: 'doc-upload-1',
      fileName: 'Police_Accident_Report_8841.pdf',
      fileSize: '2.4 MB',
      type: 'PDF',
      category: 'Police Report',
      uploadDate: new Date().toISOString(),
      url: '#',
      ocrStatus: 'Completed',
      verificationStatus: 'Verified',
      ocrFields: [
        { fieldName: 'Police Officer Name', extractedValue: 'Sgt. R. Miller (Badge #4012)', confidence: 99.2, status: 'Verified' },
        { fieldName: 'Incident Location', extractedValue: 'I-95 Southbound Exit 42', confidence: 98.7, status: 'Verified' },
        { fieldName: 'Fault Determination', extractedValue: 'Car #2 (Third Party) Failed to stop', confidence: 96.5, status: 'Verified' },
      ]
    },
    {
      id: 'doc-upload-2',
      fileName: 'Apex_Auto_Repair_Estimate.pdf',
      fileSize: '1.8 MB',
      type: 'PDF',
      category: 'Repair Estimate',
      uploadDate: new Date().toISOString(),
      url: '#',
      ocrStatus: 'Completed',
      verificationStatus: 'Verified',
      ocrFields: [
        { fieldName: 'Total Parts & Labor', extractedValue: '$18,450.00 USD', confidence: 99.8, status: 'Verified' },
        { fieldName: 'Estimated Repair Time', extractedValue: '12 Working Days', confidence: 97.4, status: 'Verified' },
      ]
    }
  ]);

  const [isUploading, setIsUploading] = useState(false);
  const [selectedDocPreview, setSelectedDocPreview] = useState<ClaimDocument | null>(null);

  const handleSimulatedFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setIsUploading(true);
      setTimeout(() => {
        const file = files[0];
        const newDoc: ClaimDocument = {
          id: `doc-${Date.now()}`,
          fileName: file.name,
          fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
          type: file.name.endsWith('.pdf') ? 'PDF' : file.name.match(/\.(jpg|png|jpeg)$/i) ? 'IMAGE' : 'WORD',
          category: 'Damage Photo',
          uploadDate: new Date().toISOString(),
          url: '#',
          ocrStatus: 'Completed',
          verificationStatus: 'Verified',
          ocrFields: [
            { fieldName: 'Document Signature', extractedValue: 'Verified Digital Timestamp', confidence: 98.0, status: 'Verified' },
            { fieldName: 'Extracted Invoice Total', extractedValue: `$${claimAmount} USD`, confidence: 96.4, status: 'Verified' }
          ]
        };
        setUploadedDocs((prev) => [...prev, newDoc]);
        setIsUploading(false);
      }, 1200);
    }
  };

  const removeDoc = (id: string) => {
    setUploadedDocs((prev) => prev.filter((d) => d.id !== id));
  };

  const handleGenerateRecommendation = (e: React.FormEvent) => {
    e.preventDefault();

    // Register claim in context
    const createdClaim = addClaim({
      title: claimTitle,
      description: claimDescription,
      category,
      priority,
      isEmergency,
      incidentDate,
      incidentTime,
      location,
      claimAmount: parseFloat(claimAmount) || 0,
      customer: {
        id: `cust-${Date.now()}`,
        name: customerName,
        phone: customerPhone,
        email: customerEmail,
        dob: customerDob,
        address: customerAddress,
        nationalId,
        memberSince: '2023-01-01',
        riskScore: 12,
      },
      policy: {
        policyNumber,
        category,
        startDate: policyStart,
        endDate: policyEnd,
        premiumStatus,
        coverageLimit: parseFloat(coverageLimit) || 50000,
        deductible: parseFloat(deductible) || 500,
        activeClaimsCount: 1,
      },
      documents: uploadedDocs,
    });

    // Reset processing steps & navigate to AI Processing Page
    setIsProcessing(true);
    setCurrentProcessingStep(0);
    router.push('/claims/processing');
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-[11px] font-bold uppercase tracking-wider">
              Step 1 of 3 &bull; Claim Intake
            </span>
            <span className="text-xs text-slate-400">Manual Officer Registration</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            New Insurance Claim Registration
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Enter verified customer details, policy coverage information, incident specifics, and upload supporting documents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 font-semibold text-xs hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => alert('Draft saved successfully!')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Draft</span>
          </button>
        </div>
      </div>

      <form onSubmit={handleGenerateRecommendation} className="space-y-6">
        
        {/* SECTION 1: Customer Information */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 border-b border-slate-200 dark:border-slate-800 pb-3">
            <User className="w-4 h-4" />
            <h3 className="font-bold text-sm uppercase tracking-wider">1. Customer Information</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Customer Name</label>
              <input
                type="text"
                required
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={customerEmail}
                onChange={(e) => setCustomerEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Phone Number</label>
              <input
                type="text"
                required
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Date of Birth</label>
              <input
                type="date"
                required
                value={customerDob}
                onChange={(e) => setCustomerDob(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">SSN / National ID</label>
              <input
                type="text"
                required
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Residential Address</label>
              <input
                type="text"
                required
                value={customerAddress}
                onChange={(e) => setCustomerAddress(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* SECTION 2: Policy Information */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 border-b border-slate-200 dark:border-slate-800 pb-3">
            <Shield className="w-4 h-4" />
            <h3 className="font-bold text-sm uppercase tracking-wider">2. Policy Information</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Policy Number</label>
              <input
                type="text"
                required
                value={policyNumber}
                onChange={(e) => setPolicyNumber(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Insurance Type</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as InsuranceCategory)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="Vehicle">Vehicle Insurance</option>
                <option value="Health">Health Insurance</option>
                <option value="Home">Home & Property</option>
                <option value="Travel">Travel Insurance</option>
                <option value="Business">Business Liability</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Coverage Limit ($)</label>
              <input
                type="number"
                value={coverageLimit}
                onChange={(e) => setCoverageLimit(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-semibold focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Standard Deductible ($)</label>
              <input
                type="number"
                value={deductible}
                onChange={(e) => setDeductible(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-semibold focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Policy Start Date</label>
              <input
                type="date"
                value={policyStart}
                onChange={(e) => setPolicyStart(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Policy End Date</label>
              <input
                type="date"
                value={policyEnd}
                onChange={(e) => setPolicyEnd(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Premium Status</label>
              <select
                value={premiumStatus}
                onChange={(e) => setPremiumStatus(e.target.value as any)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="Paid">Paid (Current)</option>
                <option value="Pending">Pending Payment</option>
                <option value="Grace Period">Grace Period</option>
                <option value="Overdue">Overdue (Warning)</option>
              </select>
            </div>
          </div>
        </div>

        {/* SECTION 3: Claim Information */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-teal-600 dark:text-teal-400 border-b border-slate-200 dark:border-slate-800 pb-3">
            <FileText className="w-4 h-4" />
            <h3 className="font-bold text-sm uppercase tracking-wider">3. Claim Incident Details</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="md:col-span-2">
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Claim Title / Short Summary</label>
              <input
                type="text"
                required
                value={claimTitle}
                onChange={(e) => setClaimTitle(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-semibold focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Requested Claim Amount ($)</label>
              <input
                type="number"
                required
                value={claimAmount}
                onChange={(e) => setClaimAmount(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-extrabold text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="md:col-span-3">
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Detailed Incident Description</label>
              <textarea
                rows={3}
                required
                value={claimDescription}
                onChange={(e) => setClaimDescription(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white leading-relaxed focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Incident Date</label>
              <input
                type="date"
                required
                value={incidentDate}
                onChange={(e) => setIncidentDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Incident Time</label>
              <input
                type="time"
                value={incidentTime}
                onChange={(e) => setIncidentTime(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Incident Location / City</label>
              <input
                type="text"
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Priority Level</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as ClaimPriority)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-semibold focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="Low">Low Priority</option>
                <option value="Medium">Medium Priority</option>
                <option value="High">High Priority</option>
                <option value="Emergency">Emergency</option>
              </select>
            </div>

            <div className="flex items-center gap-3 pt-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isEmergency}
                  onChange={(e) => setIsEmergency(e.target.checked)}
                  className="rounded border-slate-800 text-rose-600 focus:ring-rose-500 w-4 h-4"
                />
                <span className="font-bold text-rose-500 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> Emergency Escalation Mode
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* SECTION 4: Document Upload & OCR Simulator */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
              <UploadCloud className="w-4 h-4" />
              <h3 className="font-bold text-sm uppercase tracking-wider">4. Document Upload & Live OCR Extraction</h3>
            </div>
            <span className="text-[11px] text-slate-400">Supported: PDF, JPG, PNG, DOCX (Max 25MB)</span>
          </div>

          {/* Drag & Drop Area */}
          <div className="relative border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-indigo-500 dark:hover:border-indigo-500 rounded-2xl p-8 text-center transition-all bg-slate-50/50 dark:bg-slate-900/40 group">
            <input
              type="file"
              onChange={handleSimulatedFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center group-hover:scale-110 transition-transform">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Click to browse or drag & drop claim documents here
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Police accident reports, hospital discharge notes, repair estimates, damage photographs
                </p>
              </div>
            </div>
          </div>

          {isUploading && (
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center gap-3 text-xs text-indigo-400">
              <div className="w-4 h-4 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin"></div>
              <span>Uploading document & executing OCR data extraction...</span>
            </div>
          )}

          {/* Uploaded Documents List */}
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">Uploaded Claim Attachments ({uploadedDocs.length})</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {uploadedDocs.map((doc) => (
                <div key={doc.id} className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500 mt-0.5">
                      <File className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-900 dark:text-white truncate max-w-[200px]">{doc.fileName}</p>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                        <span>{doc.fileSize}</span>
                        <span>&bull;</span>
                        <span className="font-semibold text-emerald-500 flex items-center gap-0.5">
                          <CheckCircle2 className="w-2.5 h-2.5" /> OCR Verified
                        </span>
                      </div>

                      {/* OCR Fields Badge */}
                      {doc.ocrFields && doc.ocrFields.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {doc.ocrFields.slice(0, 2).map((field, idx) => (
                            <div key={idx} className="text-[10px] text-slate-400 bg-slate-200/60 dark:bg-slate-800 px-2 py-0.5 rounded flex items-center justify-between">
                              <span className="truncate">{field.fieldName}:</span>
                              <span className="font-mono font-bold text-indigo-400 ml-1">{field.extractedValue}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setSelectedDocPreview(doc)}
                      className="p-1 rounded text-slate-400 hover:text-indigo-400 transition-colors"
                      title="Preview Document"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => removeDoc(doc.id)}
                      className="p-1 rounded text-slate-400 hover:text-rose-500 transition-colors"
                      title="Delete Document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons Footer */}
        <div className="p-6 rounded-2xl glass-panel border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900 to-purple-950/40 flex items-center justify-between">
          <div>
            <h4 className="font-bold text-sm text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
              <span>Ready for Multi-Agent AI Recommendation</span>
            </h4>
            <p className="text-xs text-slate-300">
              Clicking will trigger 7 specialized agents (Intake, Policy, LangMem, RAG Search, Fraud Detection, Recommendation).
            </p>
          </div>

          <button
            type="submit"
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-extrabold text-xs shadow-xl shadow-indigo-600/30 transition-all hover:scale-[1.03]"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate AI Recommendation</span>
          </button>
        </div>

      </form>

      {/* Document Preview Modal */}
      {selectedDocPreview && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-2xl p-6 rounded-3xl border border-slate-800 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <File className="w-4 h-4 text-indigo-400" />
                <h3 className="font-bold text-sm text-white">{selectedDocPreview.fileName}</h3>
              </div>
              <button
                onClick={() => setSelectedDocPreview(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Extracted OCR Metadata</h4>
              {selectedDocPreview.ocrFields?.map((f, i) => (
                <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">{f.fieldName}</span>
                  <span className="font-mono font-bold text-white">{f.extractedValue}</span>
                </div>
              ))}
            </div>

            <div className="text-right">
              <button
                onClick={() => setSelectedDocPreview(null)}
                className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
