export type InsuranceCategory = 'Vehicle' | 'Health' | 'Home' | 'Travel' | 'Business';

export type ClaimStatus = 'Draft' | 'Submitted' | 'Processing' | 'Under Review' | 'Approved' | 'Rejected' | 'Requires Documents';

export type ClaimPriority = 'Low' | 'Medium' | 'High' | 'Emergency';

export type DocumentType = 'PDF' | 'IMAGE' | 'WORD';

export type DocumentCategory = 
  | 'Medical Report' 
  | 'Police Report' 
  | 'Invoice / Receipt' 
  | 'Damage Photo' 
  | 'Policy Schedule' 
  | 'Repair Estimate' 
  | 'ID Proof';

export interface Customer {
  id: string;
  name: string;
  phone: string;
  email: string;
  dob: string;
  address: string;
  nationalId: string;
  memberSince: string;
  riskScore: number;
}

export interface Policy {
  policyNumber: string;
  category: InsuranceCategory;
  startDate: string;
  endDate: string;
  premiumStatus: 'Paid' | 'Pending' | 'Grace Period' | 'Overdue';
  coverageLimit: number;
  deductible: number;
  activeClaimsCount: number;
}

export interface OCRField {
  fieldName: string;
  extractedValue: string;
  confidence: number;
  status: 'Verified' | 'Flagged' | 'Extracted';
}

export interface ClaimDocument {
  id: string;
  fileName: string;
  fileSize: string;
  type: DocumentType;
  category: DocumentCategory;
  uploadDate: string;
  url: string;
  ocrStatus: 'Pending' | 'In Progress' | 'Completed' | 'Failed';
  verificationStatus: 'Verified' | 'Flagged' | 'Mismatch' | 'Pending';
  ocrFields?: OCRField[];
  visionAnalysis?: any;
}

export interface AIAgentStep {
  id: string;
  agentName: 'Intake Agent' | 'Policy Validation Agent' | 'Claim History Agent' | 'Memory Agent (LangMem)' | 'RAG Knowledge Search' | 'Fraud Detection Agent' | 'Recommendation Agent';
  status: 'Pending' | 'Running' | 'Completed' | 'Warning' | 'Failed';
  timestamp: string;
  durationMs: number;
  outputSummary: string;
  details?: Record<string, any>;
}

export interface LangMemNode {
  id: string;
  claimId: string;
  summary: string;
  similarityScore: number;
  relevanceReason: string;
  resolutionOutcome: 'Approved' | 'Rejected';
  resolvedAmount: number;
  date: string;
  tags: string[];
}

export interface RAGDocument {
  id: string;
  policyTitle: string;
  sectionCode: string;
  clause: string;
  matchScore: number;
  excerpt: string;
  url?: string;
}

export interface ToolCallLog {
  toolName: string;
  args: Record<string, any>;
  result: string;
  executionTimeMs: number;
}

export interface AIRecommendation {
  verdict: 'Approve' | 'Reject' | 'Request Additional Documents';
  confidenceScore: number; // 0 to 100
  fraudRiskScore: number; // 0 to 100
  recommendedAmount: number;
  reasoningSummary: string;
  keyFindings: string[];
  riskFlags: string[];
  retrievedMemories: LangMemNode[];
  retrievedKnowledge: RAGDocument[];
  toolCalls: ToolCallLog[];
}

export interface Claim {
  id: string;
  claimNumber: string;
  title: string;
  description: string;
  category: InsuranceCategory;
  priority: ClaimPriority;
  isEmergency: boolean;
  status: ClaimStatus;
  incidentDate: string;
  incidentTime: string;
  location: string;
  claimAmount: number;
  approvedAmount?: number;
  createdAt: string;
  updatedAt: string;
  assignedOfficer: string;
  customer: Customer;
  policy: Policy;
  documents: ClaimDocument[];
  agentSteps: AIAgentStep[];
  aiRecommendation?: AIRecommendation;
  officerNotes?: string;
  humanDecision?: {
    action: 'Approve' | 'Reject' | 'Request Additional Documents';
    decidedBy: string;
    decidedAt: string;
    reason: string;
  };
}

export interface AuditLog {
  id: string;
  timestamp: string;
  claimId: string;
  claimNumber: string;
  actorType: 'Officer' | 'AI Agent';
  actorName: string;
  action: string;
  details: string;
  memoryUsed?: string;
  knowledgeUsed?: string;
  toolsCalled?: string[];
  ipAddress?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  type: 'info' | 'warning' | 'success' | 'alert';
  read: boolean;
  claimId?: string;
}
