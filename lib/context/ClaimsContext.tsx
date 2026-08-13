'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Claim, ClaimDocument, AuditLog, NotificationItem, ClaimStatus } from '@/types/insurance';
import { mockClaims, mockAuditLogs, mockNotifications } from '@/lib/data/mockData';

interface ClaimsContextType {
  claims: Claim[];
  activeClaim: Claim | null;
  setActiveClaim: (claim: Claim | null) => void;
  getClaimById: (id: string) => Claim | undefined;
  addClaim: (newClaim: Partial<Claim>) => Claim;
  updateClaimDecision: (
    claimId: string,
    action: 'Approve' | 'Reject' | 'Request Additional Documents',
    reason: string,
    decidedBy?: string
  ) => void;
  auditLogs: AuditLog[];
  notifications: NotificationItem[];
  unreadCount: number;
  markNotificationRead: (id: string) => void;
  isNotificationDrawerOpen: boolean;
  setIsNotificationDrawerOpen: (open: boolean) => void;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
  currentProcessingStep: number;
  setCurrentProcessingStep: (step: number) => void;
}

const ClaimsContext = createContext<ClaimsContextType | undefined>(undefined);

export const ClaimsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [claims, setClaims] = useState<Claim[]>(mockClaims);
  const [activeClaim, setActiveClaim] = useState<Claim | null>(mockClaims[0]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(mockAuditLogs);
  const [notifications, setNotifications] = useState<NotificationItem[]>(mockNotifications);
  const [isNotificationDrawerOpen, setIsNotificationDrawerOpen] = useState<boolean>(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentProcessingStep, setCurrentProcessingStep] = useState<number>(0);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedTheme = localStorage.getItem('theme') as 'dark' | 'light';
      if (storedTheme) {
        setTheme(storedTheme);
        document.documentElement.classList.toggle('dark', storedTheme === 'dark');
      } else {
        document.documentElement.classList.add('dark');
      }
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('theme', nextTheme);
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
  };

  const getClaimById = (id: string): Claim | undefined => {
    return claims.find((c) => c.id === id || c.claimNumber === id);
  };

  const addClaim = (newClaimData: Partial<Claim>): Claim => {
    const id = `claim-${Date.now()}`;
    const claimNumber = `CLM-2026-${Math.floor(1000 + Math.random() * 9000)}`;
    const now = new Date().toISOString();

    const createdClaim: Claim = {
      id,
      claimNumber,
      title: newClaimData.title || 'Untitled Claim',
      description: newClaimData.description || '',
      category: newClaimData.category || 'Vehicle',
      priority: newClaimData.priority || 'Medium',
      isEmergency: newClaimData.isEmergency || false,
      status: 'Submitted',
      incidentDate: newClaimData.incidentDate || new Date().toISOString().split('T')[0],
      incidentTime: newClaimData.incidentTime || '12:00',
      location: newClaimData.location || 'Unspecified Location',
      claimAmount: newClaimData.claimAmount || 0,
      createdAt: now,
      updatedAt: now,
      assignedOfficer: 'Officer Sarah Jenkins',
      customer: newClaimData.customer || {
        id: `cust-${Date.now()}`,
        name: 'Jane Doe',
        phone: '+1 (555) 000-0000',
        email: 'jane.doe@example.com',
        dob: '1990-01-01',
        address: '100 Main St, Cityville',
        nationalId: 'SSN-XXX-XX-0000',
        memberSince: '2025-01-01',
        riskScore: 10,
      },
      policy: newClaimData.policy || {
        policyNumber: `POL-${(newClaimData.category || 'VEH').substring(0, 3).toUpperCase()}-${Math.floor(10000 + Math.random() * 90000)}`,
        category: newClaimData.category || 'Vehicle',
        startDate: '2026-01-01',
        endDate: '2027-01-01',
        premiumStatus: 'Paid',
        coverageLimit: 50000,
        deductible: 500,
        activeClaimsCount: 1,
      },
      documents: newClaimData.documents || [],
      agentSteps: [
        {
          id: `step-1-${Date.now()}`,
          agentName: 'Intake Agent',
          status: 'Completed',
          timestamp: now,
          durationMs: 350,
          outputSummary: 'Parsed claim intake form & customer identification.'
        },
        {
          id: `step-2-${Date.now()}`,
          agentName: 'Policy Validation Agent',
          status: 'Completed',
          timestamp: now,
          durationMs: 410,
          outputSummary: 'Verified active policy window & coverage limits.'
        },
        {
          id: `step-3-${Date.now()}`,
          agentName: 'Claim History Agent',
          status: 'Completed',
          timestamp: now,
          durationMs: 500,
          outputSummary: 'Retrieved customer historical record.'
        },
        {
          id: `step-4-${Date.now()}`,
          agentName: 'Memory Agent (LangMem)',
          status: 'Completed',
          timestamp: now,
          durationMs: 780,
          outputSummary: 'Scanned vector memory store for similar past cases.'
        },
        {
          id: `step-5-${Date.now()}`,
          agentName: 'RAG Knowledge Search',
          status: 'Completed',
          timestamp: now,
          durationMs: 650,
          outputSummary: 'Retrieved matching policy clauses & coverage riders.'
        },
        {
          id: `step-6-${Date.now()}`,
          agentName: 'Fraud Detection Agent',
          status: 'Completed',
          timestamp: now,
          durationMs: 890,
          outputSummary: 'Calculated multi-factor risk score (Low Risk: 16/100).'
        },
        {
          id: `step-7-${Date.now()}`,
          agentName: 'Recommendation Agent',
          status: 'Completed',
          timestamp: now,
          durationMs: 910,
          outputSummary: 'Synthesized final verdict & payout estimate.'
        }
      ],
      aiRecommendation: {
        verdict: 'Approve',
        confidenceScore: 92.4,
        fraudRiskScore: 16,
        recommendedAmount: Math.max(0, (newClaimData.claimAmount || 0) - 500),
        reasoningSummary: 'Claim registration meets all primary coverage criteria. Documentation is consistent with policy limits.',
        keyFindings: [
          'Policy is active with no overdue premiums.',
          'Claim amount is within coverage threshold.',
          'No historical fraud indicators flagged.'
        ],
        riskFlags: [],
        retrievedMemories: [],
        retrievedKnowledge: [],
        toolCalls: []
      }
    };

    setClaims((prev) => [createdClaim, ...prev]);
    setActiveClaim(createdClaim);

    // Add Audit Log
    const newLog: AuditLog = {
      id: `log-${Date.now()}`,
      timestamp: now,
      claimId: createdClaim.id,
      claimNumber: createdClaim.claimNumber,
      actorType: 'Officer',
      actorName: 'Sarah Jenkins',
      action: 'Claim Registered',
      details: `New ${createdClaim.category} claim (${createdClaim.claimNumber}) registered manually.`,
      ipAddress: '10.240.12.89'
    };
    setAuditLogs((prev) => [newLog, ...prev]);

    return createdClaim;
  };

  const updateClaimDecision = (
    claimId: string,
    action: 'Approve' | 'Reject' | 'Request Additional Documents',
    reason: string,
    decidedBy = 'Officer Sarah Jenkins'
  ) => {
    const now = new Date().toISOString();
    let newStatus: ClaimStatus = 'Under Review';
    if (action === 'Approve') newStatus = 'Approved';
    if (action === 'Reject') newStatus = 'Rejected';
    if (action === 'Request Additional Documents') newStatus = 'Requires Documents';

    setClaims((prev) =>
      prev.map((c) => {
        if (c.id === claimId || c.claimNumber === claimId) {
          const updated = {
            ...c,
            status: newStatus,
            approvedAmount: action === 'Approve' ? (c.aiRecommendation?.recommendedAmount || c.claimAmount) : 0,
            updatedAt: now,
            humanDecision: {
              action,
              decidedBy,
              decidedAt: now,
              reason,
            },
          };
          if (activeClaim?.id === c.id) {
            setActiveClaim(updated);
          }
          return updated;
        }
        return c;
      })
    );

    // Add Audit Log
    const targetClaim = getClaimById(claimId);
    const newLog: AuditLog = {
      id: `log-${Date.now()}`,
      timestamp: now,
      claimId: claimId,
      claimNumber: targetClaim?.claimNumber || claimId,
      actorType: 'Officer',
      actorName: decidedBy,
      action: `Human Decision: ${action}`,
      details: `Officer executed ${action}. Reason: "${reason}"`,
      ipAddress: '10.240.12.89'
    };
    setAuditLogs((prev) => [newLog, ...prev]);

    // Add Notification
    const newNotif: NotificationItem = {
      id: `notif-${Date.now()}`,
      title: `Claim ${action}d`,
      message: `Claim ${targetClaim?.claimNumber} has been updated to ${newStatus}.`,
      timestamp: 'Just now',
      type: action === 'Approve' ? 'success' : action === 'Reject' ? 'alert' : 'warning',
      read: false,
      claimId
    };
    setNotifications((prev) => [newNotif, ...prev]);
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <ClaimsContext.Provider
      value={{
        claims,
        activeClaim,
        setActiveClaim,
        getClaimById,
        addClaim,
        updateClaimDecision,
        auditLogs,
        notifications,
        unreadCount,
        markNotificationRead,
        isNotificationDrawerOpen,
        setIsNotificationDrawerOpen,
        theme,
        toggleTheme,
        isProcessing,
        setIsProcessing,
        currentProcessingStep,
        setCurrentProcessingStep,
      }}
    >
      {children}
    </ClaimsContext.Provider>
  );
};

export const useClaims = () => {
  const context = useContext(ClaimsContext);
  if (!context) {
    throw new Error('useClaims must be used within a ClaimsProvider');
  }
  return context;
};
