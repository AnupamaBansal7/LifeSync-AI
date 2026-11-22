export type RoleSlug =
  | 'personal'
  | 'student'
  | 'professional'
  | 'entrepreneur'
  | 'manager'
  | 'freelancer'
  | 'teacher'
  | 'homemaker'
  | 'custom'
  | string;

export interface Role {
  id: string;
  slug: RoleSlug;
  name: string;
  description: string;
  default_modules: string[];
}

export interface UserRole {
  id: string;
  role_id: string;
  is_primary: boolean;
  context_metadata: Record<string, any>;
  role: Role;
}

export interface UserProfile {
  headline?: string;
  bio?: string;
  organization?: string;
  focus_areas: string[];
  work_hours_start: string;
  work_hours_end: string;
}

export interface UserPreference {
  timezone: string;
  language: string;
  theme: 'dark' | 'light';
  reduced_motion: boolean;
  ai_auto_approve_low_risk: boolean;
  training_data_opt_in: boolean;
  notification_settings: Record<string, boolean>;
}

export interface UserModule {
  id: string;
  module_key: string;
  is_enabled: boolean;
  config: Record<string, any>;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_onboarded: boolean;
  profile?: UserProfile;
  preferences?: UserPreference;
  roles: UserRole[];
  modules: UserModule[];
}

export interface Task {
  id: string;
  user_id: string;
  goal_id?: string;
  parent_task_id?: string;
  depends_on_id?: string;
  title: string;
  description?: string;
  role_context: string;
  category?: string;
  tags: string[];
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'todo' | 'in_progress' | 'blocked' | 'completed' | 'cancelled';
  due_date?: string;
  estimated_minutes: number;
  recurrence_rule?: string;
  completed_at?: string;
  created_by_agent?: string;
  created_at: string;
  updated_at: string;
}

export interface Milestone {
  id: string;
  goal_id: string;
  title: string;
  target_date?: string;
  is_completed: boolean;
  order_index: number;
}

export interface Goal {
  id: string;
  title: string;
  description?: string;
  horizon: 'short_term' | 'long_term';
  role_context: string;
  category?: string;
  target_date?: string;
  progress_percent: number;
  status: 'active' | 'paused' | 'completed' | 'archived';
  milestones: Milestone[];
  created_at: string;
}

export interface Habit {
  id: string;
  title: string;
  description?: string;
  role_context: string;
  frequency: 'daily' | 'weekly' | 'custom';
  target_days_per_week: number;
  reminder_time?: string;
  current_streak: number;
  longest_streak: number;
  is_active: boolean;
  completed_today?: boolean;
}

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  role_context: string;
  event_type: 'meeting' | 'time_block' | 'exam' | 'deadline' | 'personal';
  start_time: string;
  end_time: string;
  is_all_day: boolean;
  is_locked: boolean;
}

export interface DailyPlan {
  id: string;
  plan_date: string;
  summary: string;
  schedule_blocks: Array<{
    time: string;
    title: string;
    role: string;
  }>;
  ai_insights: Record<string, any>;
  status: string;
}

export interface ActionApproval {
  id: string;
  agent_run_id: string;
  agent_name: string;
  tool_name: string;
  action_summary: string;
  tool_arguments: Record<string, any>;
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'failed';
  execution_result?: Record<string, any>;
  created_at: string;
}

export interface ExecutionStep {
  step_order: number;
  agent_name: string;
  tool_name?: string;
  status: string;
  input_summary: Record<string, any>;
  output_summary: Record<string, any>;
}

export interface AgentRun {
  id: string;
  user_query: string;
  detected_intent: string;
  status: string;
  final_response?: string;
  latency_ms?: number;
  created_at: string;
  steps: ExecutionStep[];
  approvals: ActionApproval[];
}

export interface Memory {
  id: string;
  category: string;
  role_context: string;
  content: string;
  importance_score: number;
  source: string;
  consent_for_training: boolean;
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  role_context: string;
  chunk_index: number;
  content: string;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface AutomationRule {
  id: string;
  name: string;
  trigger_type: 'schedule' | 'task_overdue' | 'habit_missed' | 'deadline_approaching';
  trigger_config: Record<string, any>;
  action_type: 'notify' | 'generate_plan' | 'reschedule_suggest' | 'daily_review';
  action_config: Record<string, any>;
  requires_approval: boolean;
  is_active: boolean;
  last_triggered_at?: string;
  created_at: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  category: 'reminder' | 'deadline' | 'agent_approval' | 'insight';
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

export interface DashboardSummary {
  greeting: string;
  current_time_iso: string;
  active_role: string;
  productivity_score: number;
  metrics: {
    total_tasks: number;
    completed_tasks: number;
    pending_tasks: number;
    overdue_tasks: number;
    active_goals: number;
    active_habits: number;
    completed_habits_today: number;
    upcoming_events_count: number;
    pending_approvals_count: number;
    unread_notifications_count: number;
  };
  today_priorities: Array<{
    id: string;
    title: string;
    priority: string;
    status: string;
    due_date?: string;
    estimated_minutes: number;
    role_context: string;
  }>;
  upcoming_events: Array<{
    id: string;
    title: string;
    event_type: string;
    start_time: string;
    end_time: string;
    is_locked: boolean;
    role_context: string;
  }>;
  habits: Habit[];
  goals: Array<{
    id: string;
    title: string;
    progress_percent: number;
    horizon: string;
    milestones_count: number;
    completed_milestones: number;
  }>;
  daily_plan: {
    summary: string;
    blocks: Array<{
      time: string;
      title: string;
      role: string;
    }>;
  };
  role_highlights: Record<string, any>;
  user_name?: string;
  user_timezone?: string;
  email_intelligence?: {
    unread_count: number;
    important_count: number;
    unread_important_messages: Array<{
      id: string;
      sender: string;
      sender_name?: string;
      subject: string;
      date: string;
      snippet: string;
    }>;
    emails_needing_reply: Array<{
      id: string;
      sender: string;
      subject: string;
      snippet: string;
    }>;
    extracted_deadlines: Array<{
      subject: string;
      deadline: string;
      sender: string;
      urgency: string;
    }>;
    connected_provider?: string;
    account_email?: string;
  };
  agent_activity?: Array<{
    id: string;
    agent_name: string;
    status: string;
    assignment: string;
    started_at: string;
    completed_at?: string;
    result_summary: string;
  }>;
  proactive_insights?: Array<{
    type: 'deadline' | 'workload' | 'email' | 'habit' | 'calendar';
    urgency: 'low' | 'medium' | 'high' | 'urgent';
    title: string;
    description: string;
    action_text?: string;
    tab?: string;
  }>;
  recent_notifications: Array<{
    id: string;
    title: string;
    message: string;
    category: string;
    created_at: string;
  }>;
}

export type AICoreStatus =
  | 'initializing'
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'planning'
  | 'processing'
  | 'executing'
  | 'awaiting_approval'
  | 'completed'
  | 'error';

export interface EmailAttachment {
  name: string;
  size: string;
  type: string;
}

export interface EmailMessage {
  id: string;
  thread_id?: string;
  sender: string;
  sender_name?: string;
  recipient: string;
  subject: string;
  snippet: string;
  body?: string;
  date: string;
  is_read: boolean;
  is_starred: boolean;
  folder: 'inbox' | 'important' | 'unread' | 'sent' | 'drafts' | 'archived';
  labels: string[];
  has_attachments: boolean;
  attachments?: EmailAttachment[];
  source_provider: 'google' | 'microsoft' | 'simulation';
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  role_context: string;
  status: 'active' | 'paused' | 'completed' | 'archived';
  target_date?: string;
  notes: string[];
  decisions: Array<{ decision: string; date?: string; rationale?: string }>;
  created_at?: string;
  updated_at?: string;
}

export interface TransactionStep {
  id: string;
  plan_id: string;
  step_order: number;
  tool_name: string;
  reversibility: 'REVERSIBLE' | 'DELAYED_UNDO' | 'IRREVERSIBLE';
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  params: Record<string, any>;
  before_state: Record<string, any>;
  after_state: Record<string, any>;
  approved: boolean;
  status: 'pending' | 'executing' | 'verified' | 'failed' | 'rolled_back' | 'skipped';
  verification_result?: Record<string, any>;
  error_message?: string;
  executed_at?: string;
}

export interface TransactionPlan {
  id: string;
  user_id: string;
  intent_summary: string;
  status:
    | 'SIMULATED'
    | 'AWAITING_APPROVAL'
    | 'EXECUTING'
    | 'VERIFIED'
    | 'PARTIALLY_FAILED'
    | 'ROLLED_BACK'
    | 'CANCELLED';
  overall_risk: 'LOW' | 'MEDIUM' | 'HIGH';
  is_fully_reversible: boolean;
  can_rollback: boolean;
  created_at: string;
  executed_at?: string;
  rolled_back_at?: string;
  steps: TransactionStep[];
}

export interface ClarificationOption {
  id: string;
  label: string;
  description?: string;
  value: string;
}

export interface ClarificationCardData {
  session_id: string;
  step: number;
  estimated_total_steps: number;
  domain: string;
  question: string;
  selection_mode: 'single' | 'multi';
  options: ClarificationOption[];
  allow_custom_input: boolean;
  can_skip_and_generate: boolean;
}

