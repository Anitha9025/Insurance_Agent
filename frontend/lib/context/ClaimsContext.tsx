'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Claim, AuditLog, NotificationItem, ClaimStatus } from '@/types/insurance';
import {
  fetchClaims as apiFetchClaims,
  fetchAuditLogs as apiFetchAuditLogs,
  createClaim as apiCreateClaim,
  updateClaimDecision as apiUpdateClaimDecision,
  deleteClaim as apiDeleteClaim,
  deleteAllClaims as apiDeleteAllClaims,
  deleteAuditLog as apiDeleteAuditLog,
  deleteAllAuditLogs as apiDeleteAllAuditLogs
} from '@/lib/api';

interface ClaimsContextType {
  claims: Claim[];
  activeClaim: Claim | null;
  setActiveClaim: (claim: Claim | null) => void;
  getClaimById: (id: string) => Claim | undefined;
  refreshClaims: () => Promise<void>;
  addClaim: (newClaim: Partial<Claim>) => Promise<Claim>;
  removeClaim: (claimId: string) => Promise<void>;
  removeAllClaims: () => Promise<void>;
  updateClaimDecision: (
    claimId: string,
    action: 'Approve' | 'Reject' | 'Request Additional Documents',
    reason: string,
    decidedBy?: string
  ) => Promise<void>;

  auditLogs: AuditLog[];
  removeAuditLog: (id: string) => Promise<void>;
  clearAuditLogs: () => Promise<void>;

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
  isLoading: boolean;
  error: string | null;
}

const ClaimsContext = createContext<ClaimsContextType | undefined>(undefined);

export const ClaimsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [activeClaim, setActiveClaim] = useState<Claim | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isNotificationDrawerOpen, setIsNotificationDrawerOpen] = useState<boolean>(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentProcessingStep, setCurrentProcessingStep] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshClaims = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedClaims = await apiFetchClaims();
      setClaims(fetchedClaims);

      if (fetchedClaims.length > 0) {
        setActiveClaim((prev) => {
          if (!prev) return fetchedClaims[0];
          const found = fetchedClaims.find((c) => c.id === prev.id);
          return found || prev;
        });
      } else {
        setActiveClaim(null);
      }

      try {
        const logs = await apiFetchAuditLogs();
        setAuditLogs(logs);
      } catch (logErr) {
        console.warn('Audit logs fetch warning:', logErr);
      }
    } catch (err) {
      console.error('Failed to load claims from backend:', err);
      setError((err as Error).message || 'Failed to connect to backend server');
      setClaims([]);
      setActiveClaim(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

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
    refreshClaims();
  }, [refreshClaims]);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('theme', nextTheme);
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
  };

  const getClaimById = (id: string): Claim | undefined => {
    return claims.find((c) => c.id === id || c.claimNumber === id);
  };

  const addClaim = async (newClaimData: Partial<Claim>): Promise<Claim> => {
    try {
      const created = await apiCreateClaim({
        title: newClaimData.title || 'Untitled Claim',
        description: newClaimData.description || 'Insurance claim submission',
        category: newClaimData.category || 'Vehicle',
        priority: newClaimData.priority || 'Medium',
        is_emergency: newClaimData.isEmergency || false,
        incident_date: newClaimData.incidentDate || new Date().toISOString().split('T')[0],
        incident_time: newClaimData.incidentTime || '12:00',
        location: newClaimData.location || 'Unspecified Location',
        claim_amount: newClaimData.claimAmount || 0,
        customer_id: (newClaimData as any).customer_id || newClaimData.customer?.id,
        policy_number: (newClaimData as any).policy_number || newClaimData.policy?.policyNumber,
        customer: newClaimData.customer,
        policy: newClaimData.policy,
      });

      setClaims((prev) => [created, ...prev]);
      setActiveClaim(created);
      await refreshClaims();
      return created;
    } catch (err) {
      console.error('Error adding claim via API:', err);
      throw err;
    }
  };

  const updateClaimDecision = async (
    claimId: string,
    action: 'Approve' | 'Reject' | 'Request Additional Documents',
    reason: string,
    decidedBy = 'Officer Sarah Jenkins'
  ): Promise<void> => {
    try {
      const updated = await apiUpdateClaimDecision(claimId, action, reason, decidedBy);
      setClaims((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      if (activeClaim?.id === updated.id) {
        setActiveClaim(updated);
      }

      // Add Notification
      const newNotif: NotificationItem = {
        id: `notif-${Date.now()}`,
        title: `Claim Decision: ${action}`,
        message: `Claim ${updated.claimNumber} status updated to ${updated.status}.`,
        timestamp: 'Just now',
        type: action === 'Approve' ? 'success' : action === 'Reject' ? 'alert' : 'warning',
        read: false,
        claimId: updated.id
      };
      setNotifications((prev) => [newNotif, ...prev]);
      await refreshClaims();
    } catch (err) {
      console.error('Error updating claim decision via API:', err);
      throw err;
    }
  };

  const removeClaim = async (claimId: string): Promise<void> => {
    try {
      await apiDeleteClaim(claimId);
      await refreshClaims();
    } catch (err) {
      console.error('Error deleting claim:', err);
      throw err;
    }
  };

  const removeAllClaims = async (): Promise<void> => {
    try {
      await apiDeleteAllClaims();
      await refreshClaims();
    } catch (err) {
      console.error('Error deleting all claims:', err);
      throw err;
    }
  };

  const removeAuditLog = async (id: string): Promise<void> => {
    try {
      await apiDeleteAuditLog(id);
      setAuditLogs((prev) => prev.filter((log) => log.id !== id));
    } catch (err) {
      console.error('Error deleting audit log:', err);
      throw err;
    }
  };

  const clearAuditLogs = async (): Promise<void> => {
    try {
      await apiDeleteAllAuditLogs();
      setAuditLogs([]);
    } catch (err) {
      console.error('Error clearing audit logs:', err);
      throw err;
    }
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
        refreshClaims,
        addClaim,
        removeClaim,
        removeAllClaims,
        updateClaimDecision,
        auditLogs,
        removeAuditLog,
        clearAuditLogs,
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
        isLoading,
        error,
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
