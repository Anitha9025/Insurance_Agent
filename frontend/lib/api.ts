import { Claim, Customer, Policy, ClaimDocument, AuditLog } from '@/types/insurance';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? '/api/v1' : 'http://127.0.0.1:8000/api/v1');

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      const errorText = await response.text();
      let errorDetail = response.statusText;
      try {
        const parsed = JSON.parse(errorText);
        if (Array.isArray(parsed.detail)) {
          errorDetail = parsed.detail
            .map((d: any) => `${d.loc ? d.loc.slice(1).join('.') : 'field'}: ${d.msg}`)
            .join('; ');
        } else if (parsed.detail) {
          errorDetail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
        }
      } catch {
        // use statusText if JSON parse fails
      }
      throw new ApiError(errorDetail, response.status);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Network or connection error: ${(error as Error).message}`, 500);
  }
}

// 1. Claims APIs
export async function fetchClaims(params?: {
  category?: string;
  status?: string;
  priority?: string;
  customer_id?: string;
  policy_number?: string;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<Claim[]> {
  const query = new URLSearchParams();
  if (params?.category) query.append('category', params.category);
  if (params?.status) query.append('status', params.status);
  if (params?.priority) query.append('priority', params.priority);
  if (params?.customer_id) query.append('customer_id', params.customer_id);
  if (params?.policy_number) query.append('policy_number', params.policy_number);
  if (params?.search) query.append('search', params.search);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString() ? `?${query.toString()}` : '';
  const data = await request<any[]>(`/claims${queryString}`);
  return data.map(mapClaimResponse);
}

export async function fetchClaimById(id: string): Promise<Claim> {
  const data = await request<any>(`/claims/${id}`);
  return mapClaimResponse(data);
}

export async function createClaim(payload: {
  title: string;
  description: string;
  category: string;
  priority: string;
  is_emergency: boolean;
  incident_date: string;
  incident_time: string;
  location: string;
  claim_amount: number;
  currency?: string;
  customer_id?: string;
  policy_number?: string;
  customer?: Partial<Customer>;
  policy?: Partial<Policy>;
}): Promise<Claim> {
  const formattedPayload: any = {
    title: payload.title,
    description: payload.description,
    category: payload.category || 'Vehicle',
    priority: payload.priority || 'Medium',
    is_emergency: payload.is_emergency ?? false,
    incident_date: payload.incident_date,
    incident_time: payload.incident_time || '12:00',
    location: payload.location,
    claim_amount: Number(payload.claim_amount),
    currency: payload.currency || 'INR',
    assigned_officer: 'Officer Sarah Jenkins',
  };


  // 1. Customer Binding (ID vs Inline Customer Creation)
  if (payload.customer_id) {
    formattedPayload.customer_id = payload.customer_id;
  } else if (payload.customer && payload.customer.name) {
    formattedPayload.customer = {
      name: payload.customer.name,
      phone: payload.customer.phone || '+1 (555) 000-0000',
      email: payload.customer.email || 'customer@example.com',
      dob: payload.customer.dob || '1990-01-01',
      address: payload.customer.address || 'Unspecified Address',
      national_id: payload.customer.nationalId || (payload.customer as any).national_id || 'SSN-000-00-0000',
      member_since: payload.customer.memberSince || (payload.customer as any).member_since || new Date().toISOString().split('T')[0],
      risk_score: Number(payload.customer.riskScore ?? 10.0),
    };
  }

  // 2. Policy Binding (Number vs Inline Policy Creation)
  if (payload.policy_number) {
    formattedPayload.policy_number = payload.policy_number;
  } else if (payload.policy) {
    const polNum = payload.policy.policyNumber || (payload.policy as any).policy_number || `POL-${(payload.category || 'VEH').substring(0, 3).toUpperCase()}-${Math.floor(10000 + Math.random() * 90000)}`;
    formattedPayload.policy = {
      policy_number: polNum,
      category: payload.policy.category || payload.category || 'Vehicle',
      start_date: payload.policy.startDate || (payload.policy as any).start_date || '2026-01-01',
      end_date: payload.policy.endDate || (payload.policy as any).end_date || '2027-01-01',
      premium_status: payload.policy.premiumStatus || (payload.policy as any).premium_status || 'Paid',
      coverage_limit: Number(payload.policy.coverageLimit || (payload.policy as any).coverage_limit || 50000),
      deductible: Number(payload.policy.deductible || 500),
      active_claims_count: 1,
      customer_id: formattedPayload.customer_id,
    };
  }

  const data = await request<any>('/claims', {
    method: 'POST',
    body: JSON.stringify(formattedPayload),
  });
  return mapClaimResponse(data);
}

export async function updateClaimDecision(
  claimId: string,
  action: 'Approve' | 'Reject' | 'Request Additional Documents',
  reason: string,
  decidedBy: string = 'Officer Sarah Jenkins'
): Promise<Claim> {
  const data = await request<any>(`/claims/${claimId}/decision`, {
    method: 'PATCH',
    body: JSON.stringify({
      action: action,
      reason: reason,
      decided_by: decidedBy,
    }),
  });
  return mapClaimResponse(data);
}

export async function analyzeClaimWorkflow(claimId: string): Promise<any> {
  return await request<any>(`/claims/${claimId}/analyze`, {
    method: 'POST',
  });
}

export async function deleteClaim(claimId: string): Promise<any> {
  return await request<any>(`/claims/${claimId}`, {
    method: 'DELETE',
  });
}

export async function deleteAllClaims(): Promise<any> {
  return await request<any>('/claims/all', {
    method: 'DELETE',
  });
}


export async function uploadDocument(
  claimId: string,
  file: File,
  category?: string
): Promise<ClaimDocument> {
  const formData = new FormData();
  formData.append('file', file);
  if (category) {
    formData.append('category', category);
  }

  const response = await fetch(`${API_BASE_URL}/documents/claims/${claimId}/documents`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorDetail = response.statusText;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.detail) {
        errorDetail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
      }
    } catch {}
    throw new ApiError(errorDetail, response.status);
  }

  const data = await response.json();
  return mapDocumentResponse(data);
}

export async function triggerDocumentOcr(documentId: string): Promise<any> {
  return await request<any>(`/documents/${documentId}/ocr`, {
    method: 'POST',
  });
}

// 2. Customers APIs
export async function searchCustomers(queryStr?: string): Promise<Customer[]> {
  const query = queryStr ? `?search=${encodeURIComponent(queryStr)}` : '';
  const data = await request<any[]>(`/customers${query}`);
  return data.map(mapCustomerResponse);
}

export async function fetchCustomerById(id: string): Promise<Customer> {
  const data = await request<any>(`/customers/${id}`);
  return mapCustomerResponse(data);
}

// 3. Policies APIs
export async function searchPolicies(params?: { customer_id?: string; category?: string }): Promise<Policy[]> {
  const query = new URLSearchParams();
  if (params?.customer_id) query.append('customer_id', params.customer_id);
  if (params?.category) query.append('category', params.category);
  const qStr = query.toString() ? `?${query.toString()}` : '';
  const data = await request<any[]>(`/policies${qStr}`);
  return data.map(mapPolicyResponse);
}

export async function fetchPolicyByNumber(policyNumber: string): Promise<Policy> {
  const data = await request<any>(`/policies/${policyNumber}`);
  return mapPolicyResponse(data);
}

export async function verifyPolicy(policyNumber: string, incidentDate?: string): Promise<{
  status: 'policy_found' | 'policy_not_found' | 'policy_inactive' | 'policy_expired' | 'policy_document_unavailable' | 'policy_verification_required';
  policyNumber: string;
  policyExists: boolean;
  isActive: boolean;
  isExpired: boolean;
  category?: string;
  startDate?: string;
  endDate?: string;
  premiumStatus?: string;
  coverageLimit?: number;
  deductible?: number;
  customerId?: string;
  customerName?: string;
  customerEmail?: string;
  customerPhone?: string;
  policyDocumentAvailable: boolean;
  policyDocumentId?: string;
  policyDocumentTitle?: string;
  issues: string[];
  warnings: string[];
}> {
  return await request<any>('/policies/verify', {
    method: 'POST',
    body: JSON.stringify({
      policy_number: policyNumber,
      incident_date: incidentDate
    })
  });
}


// 4. Dashboard APIs
export async function fetchDashboardSummary(): Promise<{
  total_claims: number;
  pending_claims: number;
  approved_claims: number;
  rejected_claims: number;
  emergency_claims: number;
}> {
  return await request<any>('/dashboard/summary');
}

export async function fetchDashboardCategoryBreakdown(): Promise<{
  total: number;
  categories: { category: string; count: number; percentage: number }[];
}> {
  return await request<any>('/dashboard/category-breakdown');
}

export async function fetchDashboardClaimVolume(): Promise<{
  volume: { date: string; count: number }[];
}> {
  return await request<any>('/dashboard/claim-volume');
}

export async function fetchDashboardPriorityClaims(): Promise<Claim[]> {
  const data = await request<any[]>('/dashboard/priority-claims');
  return data.map(mapClaimResponse);
}

export async function fetchDashboardAiMetrics(): Promise<{
  status: string;
  total_agent_steps: number;
  completed_agent_steps: number;
  evaluation_dataset_available: boolean;
  note: string;
}> {
  return await request<any>('/dashboard/ai-metrics');
}

// 5. Memory Search APIs
export async function searchMemory(params?: {
  query?: string;
  claim_id?: string;
  customer_id?: string;
}): Promise<any> {
  const query = new URLSearchParams();
  if (params?.query) query.append('query', params.query);
  if (params?.claim_id) query.append('claim_id', params.claim_id);
  if (params?.customer_id) query.append('customer_id', params.customer_id);
  const qStr = query.toString() ? `?${query.toString()}` : '';
  return await request<any>(`/memory/search${qStr}`);
}

// 6. Audit Logs API
export async function fetchAuditLogs(claimId?: string): Promise<AuditLog[]> {
  const query = claimId ? `?claim_id=${claimId}` : '';
  const data = await request<any[]>(`/audit-logs${query}`);
  return data.map(mapAuditLogResponse);
}

export async function deleteAuditLog(id: string): Promise<void> {
  await request<any>(`/audit-logs/${id}`, {
    method: 'DELETE',
  });
}

export async function deleteAllAuditLogs(): Promise<void> {
  await request<any>('/audit-logs/all', {
    method: 'DELETE',
  });
}


// Phase 6: Knowledge Base RAG & Memory APIs
export async function uploadKnowledgeDocument(formData: FormData): Promise<any> {
  const url = `${API_BASE_URL}/knowledge/upload`;
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new ApiError(errText || 'Failed to upload policy document', response.status);
  }
  return await response.json();
}

export async function fetchKnowledgeDocuments(): Promise<any[]> {
  return await request<any[]>('/knowledge/documents');
}

export async function queryKnowledgeBase(query: string, category?: string): Promise<any> {
  return await request<any>('/knowledge/query', {
    method: 'POST',
    body: JSON.stringify({ query, category }),
  });
}

export async function deleteKnowledgeDocument(id: string): Promise<any> {
  return await request<any>(`/knowledge/documents/${id}`, {
    method: 'DELETE',
  });
}

export async function fetchMemories(query?: string, claimId?: string): Promise<any> {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  if (claimId) params.append('claim_id', claimId);
  const qStr = params.toString() ? `?${params.toString()}` : '';
  return await request<any>(`/memory/search${qStr}`);
}

// Data Mapping Helpers (snake_case -> camelCase)
function mapClaimResponse(data: any): Claim {
  return {
    id: data.id,
    claimNumber: data.claim_number || data.claimNumber,
    title: data.title,
    description: data.description,
    category: data.category,
    priority: data.priority,
    isEmergency: data.is_emergency ?? data.isEmergency ?? false,
    status: data.status,
    incidentDate: data.incident_date || data.incidentDate,
    incidentTime: data.incident_time || data.incidentTime,
    location: data.location,
    claimAmount: Number(data.claim_amount ?? data.claimAmount ?? 0),
    approvedAmount: data.approved_amount !== null ? Number(data.approved_amount) : undefined,
    currency: data.currency || 'INR',
    createdAt: data.created_at || data.createdAt || new Date().toISOString(),

    updatedAt: data.updated_at || data.updatedAt || new Date().toISOString(),
    assignedOfficer: data.assigned_officer || data.assignedOfficer || 'Officer Sarah Jenkins',
    customer: data.customer ? mapCustomerResponse(data.customer) : {
      id: data.customer_id || 'unknown',
      name: 'Customer Record Pending',
      phone: '',
      email: '',
      dob: '',
      address: '',
      nationalId: '',
      memberSince: '',
      riskScore: 0,
    },
    policy: data.policy ? mapPolicyResponse(data.policy) : {
      policyNumber: data.policy_number || 'unknown',
      category: data.category || 'Vehicle',
      startDate: '',
      endDate: '',
      premiumStatus: 'Paid',
      coverageLimit: 0,
      deductible: 0,
    },
    documents: (data.documents || []).map(mapDocumentResponse),
    agentSteps: data.agent_steps || [],
    aiRecommendation: data.ai_recommendation || null,
    auditLogs: data.audit_logs || [],
    officerNotes: data.officer_notes,
    humanDecisionAction: data.human_decision_action,
    humanDecisionBy: data.human_decision_by,
    humanDecisionAt: data.human_decision_at,
  };
}

function mapCustomerResponse(data: any): Customer {
  return {
    id: data.id,
    name: data.name,
    phone: data.phone,
    email: data.email,
    dob: data.dob,
    address: data.address,
    nationalId: data.national_id || data.nationalId || '',
    memberSince: data.member_since || data.memberSince || '',
    riskScore: Number(data.risk_score ?? data.riskScore ?? 0),
  };
}

function mapPolicyResponse(data: any): Policy {
  return {
    policyNumber: data.policy_number || data.policyNumber,
    category: data.category,
    startDate: data.start_date || data.startDate,
    endDate: data.end_date || data.endDate,
    premiumStatus: data.premium_status || data.premiumStatus,
    coverageLimit: Number(data.coverage_limit ?? data.coverageLimit ?? 0),
    deductible: Number(data.deductible ?? 0),
    activeClaimsCount: data.active_claims_count,
  };
}

function mapDocumentResponse(data: any): ClaimDocument {
  return {
    id: data.id,
    fileName: data.file_name || data.fileName,
    filePath: data.file_path || data.filePath,
    type: data.type,
    category: data.category,
    fileSize: data.file_size || data.fileSize || '0 KB',
    uploadDate: data.upload_date || data.uploadDate || new Date().toISOString(),
    url: data.url || '#',
    ocrStatus: data.ocr_status || data.ocrStatus || 'Pending',
    verificationStatus: data.verification_status || data.verificationStatus || 'Pending',
    ocrFields: (data.ocr_fields || data.ocrFields || []).map((f: any) => ({
      fieldName: f.field_name || f.fieldName,
      extractedValue: f.extracted_value || f.extractedValue,
      confidence: Number(f.confidence ?? 0),
      status: f.status || 'Pending',
    })),
    visionAnalysis: data.vision_analysis || data.visionAnalysis || null,
  };
}

function mapAuditLogResponse(data: any): AuditLog {
  return {
    id: data.id,
    timestamp: data.timestamp,
    claimId: data.claim_id || data.claimId,
    claimNumber: data.claim_number || data.claimNumber,
    actorType: data.actor_type || data.actorType,
    actorName: data.actor_name || data.actorName,
    action: data.action,
    details: data.details,
    memoryUsed: data.memory_used || data.memoryUsed,
    knowledgeUsed: data.knowledge_used || data.knowledgeUsed,
    ipAddress: data.ip_address || data.ipAddress,
  };
}

// ── Phase 7: Fraud Detection + Recommendation API ──────────────────────────

export async function fetchFraudAssessment(claimId: string): Promise<any> {
  return request<any>(`/fraud/claims/${claimId}/fraud-assessment`);
}

export async function fetchClaimRecommendation(claimId: string): Promise<any> {
  return request<any>(`/fraud/claims/${claimId}/recommendation`);
}

export async function fetchPhase7Analysis(claimId: string): Promise<any> {
  return request<any>(`/fraud/claims/${claimId}/phase7`);
}

export async function fetchClaimAnalysis(claimId: string): Promise<any> {
  return request<any>(`/claims/${claimId}/analysis`);
}


