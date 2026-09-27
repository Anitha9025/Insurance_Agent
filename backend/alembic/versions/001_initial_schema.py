"""Initial PostgreSQL Schema for Insurance Claim Support System

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-01 18:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Customers
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=False),
        sa.Column('email', sa.String(length=128), nullable=False),
        sa.Column('dob', sa.String(length=16), nullable=False),
        sa.Column('address', sa.String(length=256), nullable=False),
        sa.Column('national_id', sa.String(length=64), nullable=False),
        sa.Column('member_since', sa.String(length=16), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('national_id')
    )
    op.create_index('ix_customers_email', 'customers', ['email'])
    op.create_index('ix_customers_name', 'customers', ['name'])
    op.create_index('ix_customers_national_id', 'customers', ['national_id'])
    op.create_index('ix_customers_national_id_email', 'customers', ['national_id', 'email'])

    # 2. Policies
    op.create_table(
        'policies',
        sa.Column('policy_number', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('start_date', sa.String(length=16), nullable=False),
        sa.Column('end_date', sa.String(length=16), nullable=False),
        sa.Column('premium_status', sa.String(length=32), nullable=False, server_default='Paid'),
        sa.Column('coverage_limit', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('deductible', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('active_claims_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('customer_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('policy_number')
    )
    op.create_index('ix_policies_category', 'policies', ['category'])
    op.create_index('ix_policies_customer_id', 'policies', ['customer_id'])
    op.create_index('ix_policies_customer_category', 'policies', ['customer_id', 'category'])

    # 3. Claims
    op.create_table(
        'claims',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('claim_number', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False, server_default='Medium'),
        sa.Column('is_emergency', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='Submitted'),
        sa.Column('incident_date', sa.String(length=16), nullable=False),
        sa.Column('incident_time', sa.String(length=16), nullable=False),
        sa.Column('location', sa.String(length=256), nullable=False),
        sa.Column('claim_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('approved_amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('assigned_officer', sa.String(length=128), nullable=False, server_default='Officer Sarah Jenkins'),
        sa.Column('customer_id', sa.String(length=64), nullable=False),
        sa.Column('policy_number', sa.String(length=64), nullable=False),
        sa.Column('officer_notes', sa.Text(), nullable=True),
        sa.Column('human_decision_action', sa.String(length=64), nullable=True),
        sa.Column('human_decision_by', sa.String(length=128), nullable=True),
        sa.Column('human_decision_at', sa.String(length=32), nullable=True),
        sa.Column('human_decision_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_number'], ['policies.policy_number'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_number')
    )
    op.create_index('ix_claims_category', 'claims', ['category'])
    op.create_index('ix_claims_claim_number', 'claims', ['claim_number'])
    op.create_index('ix_claims_customer_id', 'claims', ['customer_id'])
    op.create_index('ix_claims_policy_number', 'claims', ['policy_number'])
    op.create_index('ix_claims_priority', 'claims', ['priority'])
    op.create_index('ix_claims_status', 'claims', ['status'])
    op.create_index('ix_claims_status_priority', 'claims', ['status', 'priority'])
    op.create_index('ix_claims_customer_status', 'claims', ['customer_id', 'status'])

    # 4. Claim Documents
    op.create_table(
        'claim_documents',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=False),
        sa.Column('file_name', sa.String(length=256), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.String(length=32), nullable=False),
        sa.Column('type', sa.String(length=16), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('upload_date', sa.String(length=32), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False, server_default='#'),
        sa.Column('ocr_status', sa.String(length=32), nullable=False, server_default='Pending'),
        sa.Column('verification_status', sa.String(length=32), nullable=False, server_default='Pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_claim_documents_category', 'claim_documents', ['category'])
    op.create_index('ix_claim_documents_claim_id', 'claim_documents', ['claim_id'])

    # 5. OCR Fields
    op.create_table(
        'ocr_fields',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('document_id', sa.String(length=64), nullable=False),
        sa.Column('field_name', sa.String(length=128), nullable=False),
        sa.Column('extracted_value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='Extracted'),
        sa.ForeignKeyConstraint(['document_id'], ['claim_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ocr_fields_document_id', 'ocr_fields', ['document_id'])

    # 6. Agent Steps
    op.create_table(
        'agent_steps',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=False),
        sa.Column('agent_name', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='Pending'),
        sa.Column('timestamp', sa.String(length=32), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_summary', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_steps_agent_name', 'agent_steps', ['agent_name'])
    op.create_index('ix_agent_steps_claim_id', 'agent_steps', ['claim_id'])

    # 7. AI Recommendations
    op.create_table(
        'ai_recommendations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=False),
        sa.Column('verdict', sa.String(length=64), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('fraud_risk_score', sa.Float(), nullable=False),
        sa.Column('recommended_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reasoning_summary', sa.Text(), nullable=False),
        sa.Column('key_findings', sa.JSON(), nullable=False),
        sa.Column('risk_flags', sa.JSON(), nullable=False),
        sa.Column('retrieved_memories', sa.JSON(), nullable=False),
        sa.Column('retrieved_knowledge', sa.JSON(), nullable=False),
        sa.Column('tool_calls', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_id')
    )
    op.create_index('ix_ai_recommendations_claim_id', 'ai_recommendations', ['claim_id'])

    # 8. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.String(length=32), nullable=False),
        sa.Column('claim_id', sa.String(length=64), nullable=True),
        sa.Column('claim_number', sa.String(length=64), nullable=True),
        sa.Column('actor_type', sa.String(length=32), nullable=False),
        sa.Column('actor_name', sa.String(length=128), nullable=False),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('memory_used', sa.String(length=256), nullable=True),
        sa.Column('knowledge_used', sa.String(length=256), nullable=True),
        sa.Column('tools_called', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_actor_type', 'audit_logs', ['actor_type'])
    op.create_index('ix_audit_logs_claim_id', 'audit_logs', ['claim_id'])
    op.create_index('ix_audit_logs_claim_number', 'audit_logs', ['claim_number'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_actor_action', 'audit_logs', ['actor_type', 'action'])

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('ai_recommendations')
    op.drop_table('agent_steps')
    op.drop_table('ocr_fields')
    op.drop_table('claim_documents')
    op.drop_table('claims')
    op.drop_table('policies')
    op.drop_table('customers')
