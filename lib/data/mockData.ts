import { Claim, AuditLog, NotificationItem, RAGDocument, LangMemNode } from '@/types/insurance';

export const mockClaims: Claim[] = [
  {
    id: 'claim-101',
    claimNumber: 'CLM-2026-8841',
    title: 'Multi-vehicle collision on Interstate 95 highway',
    description: 'Vehicle sustained heavy front bumper, hood, and radiator damage following a 3-car pileup during heavy rainfall. Third-party liability involved.',
    category: 'Vehicle',
    priority: 'Emergency',
    isEmergency: true,
    status: 'Under Review',
    incidentDate: '2026-08-01',
    incidentTime: '14:30',
    location: 'I-95 Exit 42, Philadelphia, PA',
    claimAmount: 18450.00,
    approvedAmount: 16800.00,
    createdAt: '2026-08-02T09:15:00Z',
    updatedAt: '2026-08-06T11:20:00Z',
    assignedOfficer: 'Officer Sarah Jenkins',
    customer: {
      id: 'cust-901',
      name: 'Alexander Vance',
      phone: '+1 (555) 234-5678',
      email: 'alex.vance@enterprise.com',
      dob: '1984-11-14',
      address: '742 Evergreen Terrace, Springfield, PA 19064',
      nationalId: 'SSN-XXX-XX-4891',
      memberSince: '2019-04-12',
      riskScore: 12,
    },
    policy: {
      policyNumber: 'POL-AUTO-99824',
      category: 'Vehicle',
      startDate: '2025-05-01',
      endDate: '2027-05-01',
      premiumStatus: 'Paid',
      coverageLimit: 50000.00,
      deductible: 500.00,
      activeClaimsCount: 1,
    },
    documents: [
      {
        id: 'doc-01',
        fileName: 'Police_Accident_Report_8841.pdf',
        fileSize: '2.4 MB',
        type: 'PDF',
        category: 'Police Report',
        uploadDate: '2026-08-02T10:00:00Z',
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
        id: 'doc-02',
        fileName: 'Apex_Auto_Repair_Estimate.pdf',
        fileSize: '1.8 MB',
        type: 'PDF',
        category: 'Repair Estimate',
        uploadDate: '2026-08-02T10:05:00Z',
        url: '#',
        ocrStatus: 'Completed',
        verificationStatus: 'Verified',
        ocrFields: [
          { fieldName: 'Total Parts & Labor', extractedValue: '$18,450.00 USD', confidence: 99.8, status: 'Verified' },
          { fieldName: 'Estimated Repair Time', extractedValue: '12 Working Days', confidence: 97.4, status: 'Verified' },
        ]
      },
      {
        id: 'doc-03',
        fileName: 'Front_Bumper_Damage_Photo1.jpg',
        fileSize: '4.2 MB',
        type: 'IMAGE',
        category: 'Damage Photo',
        uploadDate: '2026-08-02T10:10:00Z',
        url: 'https://images.unsplash.com/photo-1590362891991-f776e747a588?q=80&w=800&auto=format&fit=crop',
        ocrStatus: 'Completed',
        verificationStatus: 'Verified',
        ocrFields: [
          { fieldName: 'Damage Classification', extractedValue: 'Structural Frontal Collision', confidence: 94.1, status: 'Verified' },
          { fieldName: 'VIN Tag Verification', extractedValue: '1HGCR2F83HA099824 (Match)', confidence: 98.9, status: 'Verified' }
        ]
      }
    ],
    agentSteps: [
      {
        id: 'step-1',
        agentName: 'Intake Agent',
        status: 'Completed',
        timestamp: '2026-08-02T10:15:01Z',
        durationMs: 420,
        outputSummary: 'Parsed claim metadata. Verified policy holder Alexander Vance. Claim status updated to Intake Complete.'
      },
      {
        id: 'step-2',
        agentName: 'Policy Validation Agent',
        status: 'Completed',
        timestamp: '2026-08-02T10:15:02Z',
        durationMs: 380,
        outputSummary: 'Policy POL-AUTO-99824 is active. Coverage limit $50,000. Premium status: Paid. Incident date falls within active coverage window.'
      },
      {
        id: 'step-3',
        agentName: 'Claim History Agent',
        status: 'Completed',
        timestamp: '2026-08-02T10:15:03Z',
        durationMs: 610,
        outputSummary: 'Customer has 0 prior claims in last 36 months. Clean driver record.'
      },
      {
        id: 'step-4',
        agentName: 'Memory Agent (LangMem)',
        status: 'Completed',
        timestamp: '2026-08-02T10:15:04Z',
        durationMs: 890,
        outputSummary: 'Retrieved 2 similar past claims (CLM-2025-4109, CLM-2024-9120). Both resolved smoothly with subrogation against third party.'
      },
      {
        id: 'step-5',
        agentName: 'RAG Knowledge Search',
        status: 'Completed',
        timestamp: '2026-08-02T10:15:05Z',
        durationMs: 740,
        outputSummary: 'Matched Clause 4.2B (Comprehensive Collision & Third-Party Recovery Protocol). Standard deductible of $500 applies.'
      },
      {
        id: 'step-6',
        agentName: 'Fraud Detection Agent',
        status: 'Completed',
        timestamp: '2026-08-02T10:15:06Z',
        durationMs: 1120,
        outputSummary: 'Low fraud probability (Risk Score: 14/100). No overlapping claims, image metadata timestamp matches police accident report.'
      },
      {
        id: 'step-7',
        agentName: 'Recommendation Agent',
        status: 'Completed',
        timestamp: '2026-08-02T10:15:07Z',
        durationMs: 950,
        outputSummary: 'Synthesized final verdict: APPROVE payout of $17,950 after $500 deductible. Initiate subrogation against 3rd party insurer.'
      }
    ],
    aiRecommendation: {
      verdict: 'Approve',
      confidenceScore: 94.8,
      fraudRiskScore: 14,
      recommendedAmount: 17950.00,
      reasoningSummary: 'Claim is fully backed by official police accident report and matching itemized repair estimate. Policy POL-AUTO-99824 is active with no prior claim history anomalies. Subrogation potential against fault driver.',
      keyFindings: [
        'Police report unequivocally confirms third-party driver at fault.',
        'Repair estimate matches damage photos & structural collision guidelines.',
        'Policy has $50,000 coverage limit and $500 deductible.',
        'Customer risk profile is minimal (Score 12/100).'
      ],
      riskFlags: [],
      retrievedMemories: [
        {
          id: 'mem-881',
          claimId: 'CLM-2025-4109',
          summary: 'Highway collision with 3-car involvement on I-95. Police report confirmed 3rd party fault. Approved $15,200 payout with 100% subrogation recovery.',
          similarityScore: 0.94,
          relevanceReason: 'Identical road corridor, accident dynamics, and subrogation pathway.',
          resolutionOutcome: 'Approved',
          resolvedAmount: 15200.00,
          date: '2025-11-12',
          tags: ['Auto', 'Highway', 'Subrogation', 'Police Report']
        }
      ],
      retrievedKnowledge: [
        {
          id: 'rag-101',
          policyTitle: 'Auto Insurance Master Policy (Section 4.2 - Collision)',
          sectionCode: 'POL-AUTO-SEC-4.2B',
          clause: 'In the event of a multi-vehicle collision supported by a municipal police report, coverage shall be extended up to $50,000 subject to deductible deduction and subrogation pursuit.',
          matchScore: 0.96,
          excerpt: 'Section 4.2B outlines immediate authorization for auto repairs upon confirmation of official police documentation.'
        }
      ],
      toolCalls: [
        {
          toolName: 'verify_police_report_db',
          args: { reportId: 'PA-8841-POL', state: 'PA' },
          result: 'AUTHENTICATED - Issued by PA State Police Troop K on Aug 1, 2026.',
          executionTimeMs: 140
        },
        {
          toolName: 'calculate_subrogation_odds',
          args: { thirdPartyInsurer: 'Geico', faultRating: 1.0 },
          result: 'HIGH LIKELIHOOD (95%) - Full recovery expected within 45 days.',
          executionTimeMs: 220
        }
      ]
    }
  },
  {
    id: 'claim-102',
    claimNumber: 'CLM-2026-9014',
    title: 'Emergency Cardiac Surgery & Hospitalization Payout',
    description: 'Patient admitted via emergency room for acute coronary syndrome requiring stent placement and 4 days ICU admission.',
    category: 'Health',
    priority: 'Emergency',
    isEmergency: true,
    status: 'Approved',
    incidentDate: '2026-07-28',
    incidentTime: '03:15',
    location: 'St. Jude Memorial Hospital, Chicago, IL',
    claimAmount: 42300.00,
    approvedAmount: 39800.00,
    createdAt: '2026-07-29T14:20:00Z',
    updatedAt: '2026-08-05T16:45:00Z',
    assignedOfficer: 'Officer Marcus Sterling',
    customer: {
      id: 'cust-902',
      name: 'Elena Rostova',
      phone: '+1 (555) 890-1234',
      email: 'elena.rostova@healthcorp.org',
      dob: '1976-03-22',
      address: '120 Michigan Ave, Suite 400, Chicago, IL 60601',
      nationalId: 'SSN-XXX-XX-8912',
      memberSince: '2021-01-15',
      riskScore: 8,
    },
    policy: {
      policyNumber: 'POL-HLTH-77310',
      category: 'Health',
      startDate: '2026-01-01',
      endDate: '2026-12-31',
      premiumStatus: 'Paid',
      coverageLimit: 250000.00,
      deductible: 2500.00,
      activeClaimsCount: 1,
    },
    documents: [
      {
        id: 'doc-04',
        fileName: 'St_Jude_ICU_Discharge_Summary.pdf',
        fileSize: '3.1 MB',
        type: 'PDF',
        category: 'Medical Report',
        uploadDate: '2026-07-29T15:00:00Z',
        url: '#',
        ocrStatus: 'Completed',
        verificationStatus: 'Verified',
        ocrFields: [
          { fieldName: 'Diagnosis Code', extractedValue: 'ICD-10 I21.0 (STEMI)', confidence: 99.5, status: 'Verified' },
          { fieldName: 'Procedure Code', extractedValue: 'CPT 92928 (Percutaneous Coronary Angioplasty)', confidence: 99.1, status: 'Verified' },
        ]
      }
    ],
    agentSteps: [],
    aiRecommendation: {
      verdict: 'Approve',
      confidenceScore: 97.2,
      fraudRiskScore: 6,
      recommendedAmount: 39800.00,
      reasoningSummary: 'Medical documentation is complete and verified against hospital EHR database. Procedure is covered under Section 2.1 Major Medical.',
      keyFindings: ['In-network provider', 'Pre-authorization waived under Emergency Care exception'],
      riskFlags: [],
      retrievedMemories: [],
      retrievedKnowledge: [],
      toolCalls: []
    }
  },
  {
    id: 'claim-103',
    claimNumber: 'CLM-2026-7732',
    title: 'Severe Storm Damage to Residential Roof & Solar Arrays',
    description: 'Hailstorm damage resulted in cracked tiles and destroyed solar panel glass array over primary residence.',
    category: 'Home',
    priority: 'High',
    isEmergency: false,
    status: 'Requires Documents',
    incidentDate: '2026-08-03',
    incidentTime: '18:45',
    location: '1844 Birchwood Road, Austin, TX 78745',
    claimAmount: 28900.00,
    createdAt: '2026-08-04T11:10:00Z',
    updatedAt: '2026-08-06T08:30:00Z',
    assignedOfficer: 'Officer Sarah Jenkins',
    customer: {
      id: 'cust-903',
      name: 'David K. Chen',
      phone: '+1 (555) 456-7890',
      email: 'dchen@techspace.io',
      dob: '1989-06-05',
      address: '1844 Birchwood Road, Austin, TX 78745',
      nationalId: 'SSN-XXX-XX-1102',
      memberSince: '2022-09-01',
      riskScore: 28,
    },
    policy: {
      policyNumber: 'POL-HOME-44109',
      category: 'Home',
      startDate: '2025-09-01',
      endDate: '2026-09-01',
      premiumStatus: 'Paid',
      coverageLimit: 450000.00,
      deductible: 1000.00,
      activeClaimsCount: 2,
    },
    documents: [
      {
        id: 'doc-05',
        fileName: 'Roof_Inspection_Contractor_Quote.pdf',
        fileSize: '1.2 MB',
        type: 'PDF',
        category: 'Repair Estimate',
        uploadDate: '2026-08-04T12:00:00Z',
        url: '#',
        ocrStatus: 'Completed',
        verificationStatus: 'Flagged',
        ocrFields: [
          { fieldName: 'Quote Total', extractedValue: '$28,900.00', confidence: 95.0, status: 'Extracted' },
          { fieldName: 'Solar Panel Rider Specified', extractedValue: 'Not Found in baseline quote', confidence: 80.0, status: 'Flagged' }
        ]
      }
    ],
    agentSteps: [],
    aiRecommendation: {
      verdict: 'Request Additional Documents',
      confidenceScore: 82.5,
      fraudRiskScore: 35,
      recommendedAmount: 0,
      reasoningSummary: 'Roof repair estimate lacks clear itemization between solar array replacement and standard roof tile replacement. Solar rider documentation missing.',
      keyFindings: [
        'NOAA weather radar confirms hail activity in Austin 78745 zip code on Aug 3.',
        'Solar panel coverage endorsement document is required to process full $28,900 request.'
      ],
      riskFlags: ['Unclear solar panel ownership/lease agreement status.'],
      retrievedMemories: [],
      retrievedKnowledge: [],
      toolCalls: []
    }
  },
  {
    id: 'claim-104',
    claimNumber: 'CLM-2026-6190',
    title: 'Suspicious Commercial Inventory Fire & Smoke Claim',
    description: 'Nighttime warehouse fire destroying electronics inventory. Investigator detected discrepancy in fire suppression system log.',
    category: 'Business',
    priority: 'High',
    isEmergency: false,
    status: 'Rejected',
    incidentDate: '2026-07-15',
    incidentTime: '01:20',
    location: '900 Logistics Blvd, Warehouse 4B, Miami, FL',
    claimAmount: 185000.00,
    approvedAmount: 0.00,
    createdAt: '2026-07-16T08:00:00Z',
    updatedAt: '2026-07-20T14:15:00Z',
    assignedOfficer: 'Lead Adjuster Michael Thorne',
    customer: {
      id: 'cust-904',
      name: 'Vanguard Traders LLC',
      phone: '+1 (555) 777-9911',
      email: 'claims@vanguardtraders.fl',
      dob: 'N/A (Business)',
      address: '900 Logistics Blvd, Miami, FL 33166',
      nationalId: 'EIN-XX-XXX9921',
      memberSince: '2025-02-10',
      riskScore: 78,
    },
    policy: {
      policyNumber: 'POL-BIZ-11928',
      category: 'Business',
      startDate: '2025-02-10',
      endDate: '2027-02-10',
      premiumStatus: 'Overdue',
      coverageLimit: 500000.00,
      deductible: 5000.00,
      activeClaimsCount: 3,
    },
    documents: [],
    agentSteps: [],
    aiRecommendation: {
      verdict: 'Reject',
      confidenceScore: 98.4,
      fraudRiskScore: 88,
      recommendedAmount: 0,
      reasoningSummary: 'Fire marshal report indicates arson suspect indicators. Sprinkler system valves were manually turned off prior to ignition. Policy premium is currently overdue.',
      keyFindings: [
        'Fraud Risk Score: 88/100 (Extremely High)',
        'Arson investigation pending with Miami-Dade Fire Dept',
        'Lapsed premium status on date of incident'
      ],
      riskFlags: ['Manual suppression system shutdown detected', 'Multiple recent policy changes'],
      retrievedMemories: [],
      retrievedKnowledge: [],
      toolCalls: []
    }
  },
  {
    id: 'claim-105',
    claimNumber: 'CLM-2026-5541',
    title: 'International Flight Cancellation & Medical Interruption',
    description: 'Passenger hospitalized in Tokyo due to acute appendicitis, resulting in missed connection and emergency travel itinerary modification.',
    category: 'Travel',
    priority: 'Medium',
    isEmergency: false,
    status: 'Processing',
    incidentDate: '2026-08-04',
    incidentTime: '21:00',
    location: 'Haneda Airport & Tokyo Medical Center, Japan',
    claimAmount: 4850.00,
    createdAt: '2026-08-05T13:40:00Z',
    updatedAt: '2026-08-06T10:00:00Z',
    assignedOfficer: 'Officer Sarah Jenkins',
    customer: {
      id: 'cust-905',
      name: 'Samantha Wright',
      phone: '+1 (555) 321-9876',
      email: 'swright@designstudio.co',
      dob: '1992-08-19',
      address: '450 Sunset Blvd, Los Angeles, CA 90028',
      nationalId: 'SSN-XXX-XX-3341',
      memberSince: '2024-05-18',
      riskScore: 15,
    },
    policy: {
      policyNumber: 'POL-TRV-88219',
      category: 'Travel',
      startDate: '2026-07-25',
      endDate: '2026-08-15',
      premiumStatus: 'Paid',
      coverageLimit: 15000.00,
      deductible: 100.00,
      activeClaimsCount: 1,
    },
    documents: [
      {
        id: 'doc-06',
        fileName: 'Tokyo_Hospital_Hospitalization_Receipt.pdf',
        fileSize: '950 KB',
        type: 'PDF',
        category: 'Medical Report',
        uploadDate: '2026-08-05T14:00:00Z',
        url: '#',
        ocrStatus: 'Completed',
        verificationStatus: 'Verified',
        ocrFields: [
          { fieldName: 'Hospital Name', extractedValue: 'Tokyo International St. Mary Hospital', confidence: 98.4, status: 'Verified' },
          { fieldName: 'Total Bill JPY', extractedValue: '¥520,000 (Approx $3,450 USD)', confidence: 97.2, status: 'Verified' }
        ]
      }
    ],
    agentSteps: [],
  }
];

export const mockLangMemNodes: LangMemNode[] = [
  {
    id: 'mem-881',
    claimId: 'CLM-2025-4109',
    summary: 'Highway collision with 3-car involvement on I-95. Police report confirmed 3rd party fault. Approved $15,200 payout with 100% subrogation recovery.',
    similarityScore: 0.94,
    relevanceReason: 'Identical road corridor, accident dynamics, and subrogation pathway.',
    resolutionOutcome: 'Approved',
    resolvedAmount: 15200.00,
    date: '2025-11-12',
    tags: ['Auto', 'Highway', 'Subrogation', 'Police Report']
  },
  {
    id: 'mem-882',
    claimId: 'CLM-2024-9120',
    summary: 'Rear-end collision at traffic stop. Officer verified police accident record and accepted quote from Apex Auto Repair.',
    similarityScore: 0.89,
    relevanceReason: 'Same repair facility (Apex Auto) and matching labor cost benchmarks.',
    resolutionOutcome: 'Approved',
    resolvedAmount: 11400.00,
    date: '2024-08-20',
    tags: ['Auto', 'Apex Auto', 'Labor Benchmark']
  },
  {
    id: 'mem-883',
    claimId: 'CLM-2025-1092',
    summary: 'Flagged commercial property claim involving suspicious electrical fire. Investigation revealed pre-existing code violations.',
    similarityScore: 0.86,
    relevanceReason: 'High fraud pattern match (sprinkler malfunction + overdue premium).',
    resolutionOutcome: 'Rejected',
    resolvedAmount: 0.00,
    date: '2025-04-03',
    tags: ['Business', 'Fraud Pattern', 'Arson']
  },
  {
    id: 'mem-884',
    claimId: 'CLM-2026-0312',
    summary: 'Acute medical emergency during international travel. Verified hospital records via international consular desk.',
    similarityScore: 0.91,
    relevanceReason: 'Hospital verification workflow in Asian travel corridor.',
    resolutionOutcome: 'Approved',
    resolvedAmount: 5100.00,
    date: '2026-02-14',
    tags: ['Travel', 'Medical Emergency', 'Hospital OCR']
  }
];

export const mockRAGDocuments: RAGDocument[] = [
  {
    id: 'rag-101',
    policyTitle: 'Auto Insurance Master Policy (Section 4.2 - Collision)',
    sectionCode: 'POL-AUTO-SEC-4.2B',
    clause: 'In the event of a multi-vehicle collision supported by a municipal police report, coverage shall be extended up to $50,000 subject to deductible deduction and subrogation pursuit.',
    matchScore: 0.96,
    excerpt: 'Section 4.2B outlines immediate authorization for auto repairs upon confirmation of official police documentation.'
  },
  {
    id: 'rag-102',
    policyTitle: 'Subrogation & Third-Party Recourse Standards',
    sectionCode: 'STD-SUBRO-2026-V1',
    clause: 'When police documentation identifies a non-policyholder as 100% liable, the claim intake officer may issue interim approval while initiating automated subrogation claims against the third-party insurer.',
    matchScore: 0.92,
    excerpt: 'Allows fast-tracked payout authorization when subrogation probability index exceeds 85%.'
  },
  {
    id: 'rag-103',
    policyTitle: 'Health Care Emergency Waiver Protocol',
    sectionCode: 'POL-HLTH-SEC-2.1E',
    clause: 'Pre-authorization for inpatient surgical procedures is waived in life-threatening emergency admissions certified by an accredited emergency department physician.',
    matchScore: 0.98,
    excerpt: 'Waives 72-hour pre-approval requirement for STEMI and acute cardiac interventions.'
  },
  {
    id: 'rag-104',
    policyTitle: 'Property & Roof Hail Rider Endorsement',
    sectionCode: 'POL-HOME-RIDER-88',
    clause: 'Solar panel roof arrays require explicit supplemental endorsement rider document POL-HOME-SOLAR-A to qualify for full glass replacement compensation.',
    matchScore: 0.89,
    excerpt: 'Requires submission of solar lease or ownership certificate before disbursing funds exceeding $20,000.'
  }
];

export const mockAuditLogs: AuditLog[] = [
  {
    id: 'log-501',
    timestamp: '2026-08-06T11:20:00Z',
    claimId: 'claim-101',
    claimNumber: 'CLM-2026-8841',
    actorType: 'Officer',
    actorName: 'Sarah Jenkins',
    action: 'Claim Decision Updated',
    details: 'Officer Sarah Jenkins moved status to Under Review after reviewing Recommendation Agent verdict (Approve $17,950).',
    memoryUsed: 'mem-881 (CLM-2025-4109)',
    knowledgeUsed: 'POL-AUTO-SEC-4.2B',
    toolsCalled: ['verify_police_report_db', 'calculate_subrogation_odds'],
    ipAddress: '10.240.12.89'
  },
  {
    id: 'log-502',
    timestamp: '2026-08-02T10:15:07Z',
    claimId: 'claim-101',
    claimNumber: 'CLM-2026-8841',
    actorType: 'AI Agent',
    actorName: 'Recommendation Agent',
    action: 'AI Recommendation Generated',
    details: 'Synthesized final verdict: APPROVE payout of $17,950 after $500 deductible. Confidence 94.8%, Fraud Score 14.',
    memoryUsed: 'mem-881, mem-882',
    knowledgeUsed: 'POL-AUTO-SEC-4.2B, STD-SUBRO-2026-V1',
    toolsCalled: ['verify_police_report_db', 'calculate_subrogation_odds']
  },
  {
    id: 'log-503',
    timestamp: '2026-08-02T10:15:06Z',
    claimId: 'claim-101',
    claimNumber: 'CLM-2026-8841',
    actorType: 'AI Agent',
    actorName: 'Fraud Detection Agent',
    action: 'Fraud Risk Analysis Completed',
    details: 'Scored claim at 14/100 (Low Risk). Metadata verification clean.',
    memoryUsed: 'mem-883'
  },
  {
    id: 'log-504',
    timestamp: '2026-08-02T10:05:00Z',
    claimId: 'claim-101',
    claimNumber: 'CLM-2026-8841',
    actorType: 'Officer',
    actorName: 'Sarah Jenkins',
    action: 'Document Upload & OCR Triggered',
    details: 'Uploaded Police_Accident_Report_8841.pdf and Apex_Auto_Repair_Estimate.pdf. OCR status set to Completed.',
    ipAddress: '10.240.12.89'
  }
];

export const mockNotifications: NotificationItem[] = [
  {
    id: 'notif-1',
    title: 'AI Processing Complete',
    message: 'Recommendation Agent finished evaluation for Claim CLM-2026-8841 (Verdict: Approve $17,950).',
    timestamp: '10 mins ago',
    type: 'success',
    read: false,
    claimId: 'claim-101'
  },
  {
    id: 'notif-2',
    title: 'High Fraud Alert Flagged',
    message: 'Fraud Agent flagged Claim CLM-2026-6190 (Vanguard Traders LLC) with high risk score 88/100.',
    timestamp: '1 hour ago',
    type: 'alert',
    read: false,
    claimId: 'claim-104'
  },
  {
    id: 'notif-3',
    title: 'Document Required Warning',
    message: 'Claim CLM-2026-7732 requires Solar Endorsement Rider document to proceed.',
    timestamp: '3 hours ago',
    type: 'warning',
    read: true,
    claimId: 'claim-103'
  }
];
