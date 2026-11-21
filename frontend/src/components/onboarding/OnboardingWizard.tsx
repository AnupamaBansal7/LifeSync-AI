import React, { useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  Check,
  CheckCircle2,
  Compass,
  GraduationCap,
  Heart,
  Target,
  User as UserIcon,
} from 'lucide-react';
import type { Role, User } from '../../types';

interface OnboardingWizardProps {
  user: User;
  rolesCatalog: Role[];
  onComplete: (data: any) => Promise<void>;
  loading: boolean;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  user,
  rolesCatalog,
  onComplete,
  loading,
}) => {
  const [step, setStep] = useState(1);

  // Step 1: Basic Info
  const [fullName, setFullName] = useState(user.full_name || '');
  const [avatarIndex, setAvatarIndex] = useState(0);
  const [timezone, setTimezone] = useState(
    user.preferences?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  );

  // Step 2 & 3: Primary Role (guaranteed personal by default) & Additional Roles
  const [primaryRole, setPrimaryRole] = useState('personal');
  const [selectedRoles, setSelectedRoles] = useState<string[]>(['personal', 'student']);

  // Step 4: Role-specific contextual data
  const [studentData, setStudentData] = useState({
    institution: '',
    course: '',
    semester: 'Final Year',
    subjects: 'AI Systems, Distributed Computing, Database Design',
    studyTargetHours: '3 hours/day',
  });

  const [professionalData, setProfessionalData] = useState({
    organization: '',
    designation: 'Software Engineer',
    workHoursStart: '09:00',
    workHoursEnd: '18:00',
    professionalGoals: 'Lead architectural redesign and ship core product',
  });

  const [entrepreneurData, setEntrepreneurData] = useState({
    businessName: '',
    businessObjectives: 'Acquire 100 paid beta customers and achieve profitability',
    currentPriorities: 'Product refinement, growth experiments, hiring core team',
  });

  const [customData, setCustomData] = useState({
    roleName: '',
    responsibilities: '',
  });

  // Step 5: Goals, Preferences & Routines
  const [shortTermGoal, setShortTermGoal] = useState('Build and ship LifeSync AI Capstone OS');
  const [longTermGoal, setLongTermGoal] = useState('Become a high-impact AI Systems Architect');
  const [morningRoutine, setMorningRoutine] = useState('60m deep focus review + wellness check');
  const [workHoursStart, setWorkHoursStart] = useState('09:00');
  const [workHoursEnd, setWorkHoursEnd] = useState('18:00');
  const [trainingDataOptIn, setTrainingDataOptIn] = useState(false);

  // Step 6: Modules Toggling
  const defaultModulesList = [
    { key: 'tasks', name: 'Task Management', desc: 'Priorities, Kanban boards, subtasks', core: true },
    { key: 'calendar', name: 'Smart Calendar & Plans', desc: 'Time blocks, schedules, daily plans', core: true },
    { key: 'goals', name: 'Goals & Milestones', desc: 'Progress tracking, horizon roadmap', core: true },
    { key: 'habits', name: 'Habits & Streaks', desc: 'Consistency tracking and streak nudges', core: true },
    { key: 'memory', name: 'Personal Memory & RAG', desc: 'Semantic context and knowledge library', core: true },
    { key: 'automations', name: 'Automations Engine', desc: 'Scheduled workflows and event triggers', core: false },
    { key: 'analytics', name: 'Productivity Analytics', desc: 'Recharts trends, workload distribution', core: false },
  ];

  const [enabledModules, setEnabledModules] = useState<string[]>([
    'tasks',
    'calendar',
    'goals',
    'habits',
    'memory',
    'automations',
    'analytics',
  ]);

  const avatarGradients = [
    'from-indigo-500 to-violet-600',
    'from-cyan-500 to-blue-600',
    'from-emerald-500 to-teal-600',
    'from-rose-500 to-orange-500',
    'from-purple-500 to-pink-600',
  ];

  const handleToggleRole = (slug: string) => {
    if (slug === 'personal') {
      // Personal must always remain enabled
      return;
    }
    if (selectedRoles.includes(slug)) {
      setSelectedRoles(selectedRoles.filter((s) => s !== slug));
      if (primaryRole === slug) {
        setPrimaryRole('personal');
      }
    } else {
      setSelectedRoles([...selectedRoles, slug]);
    }
  };

  const handleToggleModule = (key: string, isCore: boolean) => {
    if (isCore) return; // Core modules remain active
    if (enabledModules.includes(key)) {
      setEnabledModules(enabledModules.filter((m) => m !== key));
    } else {
      setEnabledModules([...enabledModules, key]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Prepare role payload
    const rolesPayload = selectedRoles.map((slug) => {
      let meta: Record<string, any> = {};
      if (slug === 'student') meta = studentData;
      else if (slug === 'professional') meta = professionalData;
      else if (slug === 'entrepreneur') meta = entrepreneurData;
      else if (slug === 'custom') meta = customData;

      return {
        role_slug: slug,
        is_primary: slug === primaryRole,
        context_metadata: meta,
      };
    });

    const payload = {
      roles: rolesPayload,
      headline:
        selectedRoles.includes('student')
          ? `${studentData.course || 'Student'} • ${studentData.institution || 'University'}`
          : selectedRoles.includes('professional')
          ? `${professionalData.designation} at ${professionalData.organization || 'Company'}`
          : 'Personal Life Builder',
      organization:
        professionalData.organization || studentData.institution || entrepreneurData.businessName || '',
      focus_areas: [
        studentData.subjects,
        professionalData.professionalGoals,
        entrepreneurData.currentPriorities,
      ]
        .filter(Boolean)
        .flatMap((s) => s.split(',').map((x) => x.trim()))
        .filter(Boolean),
      work_hours_start: workHoursStart,
      work_hours_end: workHoursEnd,
      morning_routine: morningRoutine,
      timezone,
      training_data_opt_in: trainingDataOptIn,
      enabled_modules: enabledModules,
      initial_goals: [shortTermGoal, longTermGoal].filter(Boolean),
    };

    await onComplete(payload);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-slate-950 via-indigo-950/20 to-slate-950 text-slate-100 select-none">
      <div className="w-full max-w-3xl rounded-3xl bg-slate-900/90 border border-slate-800 shadow-2xl p-6 sm:p-10 backdrop-blur-2xl">
        {/* Progress Stepper Header */}
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Compass className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-indigo-400">
                Step {step} of 6
              </div>
              <h2 className="text-lg font-bold">
                {step === 1 && 'Basic Information'}
                {step === 2 && 'Primary Operating Role'}
                {step === 3 && 'Secondary & Active Roles'}
                {step === 4 && 'Role Personalization'}
                {step === 5 && 'Goals & Routines'}
                {step === 6 && 'Module Configuration'}
              </h2>
            </div>
          </div>

          <div className="flex gap-1.5">
            {[1, 2, 3, 4, 5, 6].map((s) => (
              <div
                key={s}
                className={`w-7 h-1.5 rounded-full transition-all ${
                  s === step ? 'bg-indigo-500 shadow-sm' : s < step ? 'bg-indigo-800' : 'bg-slate-800'
                }`}
              />
            ))}
          </div>
        </div>

        <form onSubmit={step === 6 ? handleSubmit : (e) => { e.preventDefault(); setStep(step + 1); }}>
          {/* STEP 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-6">
              <p className="text-sm text-slate-400">
                Confirm your identity and local time zone. LifeSync AI coordinates tasks and scheduling blocks around your local clock.
              </p>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-2">Avatar Color</label>
                <div className="flex items-center gap-3">
                  {avatarGradients.map((grad, idx) => (
                    <button
                      type="button"
                      key={idx}
                      onClick={() => setAvatarIndex(idx)}
                      className={`w-10 h-10 rounded-full bg-gradient-to-tr ${grad} flex items-center justify-center text-white transition-all cursor-pointer ${
                        avatarIndex === idx ? 'ring-2 ring-white scale-110 shadow-lg' : 'opacity-70 hover:opacity-100'
                      }`}
                    >
                      {avatarIndex === idx && <Check className="w-4 h-4" />}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Full Name</label>
                <input
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Anupama Bansal"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Time Zone</label>
                <input
                  required
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm font-mono text-slate-300 focus:border-indigo-500 outline-none"
                />
              </div>
            </div>
          )}

          {/* STEP 2: Primary Role (Default Personal) */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold mb-2">
                  <Heart className="w-3.5 h-3.5 text-rose-400" /> Default Primary: PERSONAL
                </span>
                <p className="text-sm text-slate-300 leading-relaxed">
                  Every user is an individual first. LifeSync AI ensures your personal health, daily habits, reading, and wellness remain the central anchor of your life management operating system.
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 flex items-start gap-4">
                <div className="p-3 rounded-xl bg-indigo-600/30 text-indigo-300 shrink-0">
                  <UserIcon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-white">Personal Life & Wellness (Default Primary)</h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Daily routines, sleep targets, fitness consistency, personal finance check-ins, and life admin.
                  </p>
                  <div className="mt-3 text-[11px] text-emerald-400 flex items-center gap-1.5 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Guaranteed active as primary life anchor
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Additional Roles */}
          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                Select all additional identities and responsibilities you balance simultaneously. LifeSync will activate specialized AI agents for each:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-96 overflow-y-auto p-1">
                {rolesCatalog.map((role) => {
                  const isSelected = selectedRoles.includes(role.slug);
                  const isPersonal = role.slug === 'personal';
                  return (
                    <button
                      type="button"
                      key={role.slug}
                      onClick={() => handleToggleRole(role.slug)}
                      className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                          : 'bg-slate-950/70 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-sm">{role.name}</span>
                        {isSelected && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                      </div>
                      <p className="text-xs opacity-75 line-clamp-2">{role.description}</p>
                      {isPersonal && (
                        <span className="mt-2 inline-block text-[10px] text-indigo-300 font-mono">
                          Primary Anchor
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 4: Role-Specific Personalization */}
          {step === 4 && (
            <div className="space-y-6 max-h-[420px] overflow-y-auto p-1">
              <p className="text-sm text-slate-400">
                Provide operational context for your selected roles so AI agents can offer precision assistance:
              </p>

              {/* Student Section */}
              {selectedRoles.includes('student') && (
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
                    <GraduationCap className="w-4 h-4" /> Student & Academic Details
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Institution</label>
                      <input
                        value={studentData.institution}
                        onChange={(e) => setStudentData({ ...studentData, institution: e.target.value })}
                        placeholder="e.g. Stanford / IIT / University"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Course & Degree</label>
                      <input
                        value={studentData.course}
                        onChange={(e) => setStudentData({ ...studentData, course: e.target.value })}
                        placeholder="e.g. B.Tech Computer Science"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">Subjects / Current Focus</label>
                    <input
                      value={studentData.subjects}
                      onChange={(e) => setStudentData({ ...studentData, subjects: e.target.value })}
                      placeholder="e.g. AI Systems, Networks, Algorithms"
                      className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                    />
                  </div>
                </div>
              )}

              {/* Working Professional Section */}
              {selectedRoles.includes('professional') && (
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
                    <Briefcase className="w-4 h-4" /> Working Professional Details
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Organization</label>
                      <input
                        value={professionalData.organization}
                        onChange={(e) => setProfessionalData({ ...professionalData, organization: e.target.value })}
                        placeholder="e.g. Google / Microsoft / Startup"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Designation</label>
                      <input
                        value={professionalData.designation}
                        onChange={(e) => setProfessionalData({ ...professionalData, designation: e.target.value })}
                        placeholder="e.g. Senior Software Engineer"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">Professional Goals</label>
                    <input
                      value={professionalData.professionalGoals}
                      onChange={(e) => setProfessionalData({ ...professionalData, professionalGoals: e.target.value })}
                      placeholder="e.g. Lead system architecture and deliver Q4 deliverables"
                      className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                    />
                  </div>
                </div>
              )}

              {/* Entrepreneur Section */}
              {selectedRoles.includes('entrepreneur') && (
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
                    <Target className="w-4 h-4" /> Entrepreneurial Venture
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Company / Venture Name</label>
                      <input
                        value={entrepreneurData.businessName}
                        onChange={(e) => setEntrepreneurData({ ...entrepreneurData, businessName: e.target.value })}
                        placeholder="e.g. LifeSync Labs"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Key Objectives</label>
                      <input
                        value={entrepreneurData.businessObjectives}
                        onChange={(e) => setEntrepreneurData({ ...entrepreneurData, businessObjectives: e.target.value })}
                        placeholder="e.g. 100 beta users"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Custom Role Section */}
              {selectedRoles.includes('custom') && (
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
                    <Compass className="w-4 h-4" /> Custom Responsibility
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Role Title</label>
                      <input
                        value={customData.roleName}
                        onChange={(e) => setCustomData({ ...customData, roleName: e.target.value })}
                        placeholder="e.g. Content Creator / Researcher"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Key Responsibilities</label>
                      <input
                        value={customData.responsibilities}
                        onChange={(e) => setCustomData({ ...customData, responsibilities: e.target.value })}
                        placeholder="e.g. Weekly video publishing and audience outreach"
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* STEP 5: Goals & Preferences */}
          {step === 5 && (
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                Define your foundational goals and working routine.
              </p>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Priority Short-Term Goal</label>
                <input
                  required
                  value={shortTermGoal}
                  onChange={(e) => setShortTermGoal(e.target.value)}
                  placeholder="e.g. Ship LifeSync Capstone and achieve 95% test coverage"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Long-Term Aspiration</label>
                <input
                  value={longTermGoal}
                  onChange={(e) => setLongTermGoal(e.target.value)}
                  placeholder="e.g. Become a distinguished Staff Engineer / Founder"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Daily / Morning Routine</label>
                <input
                  value={morningRoutine}
                  onChange={(e) => setMorningRoutine(e.target.value)}
                  placeholder="e.g. 60m deep focus review + wellness check"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Work Start Time</label>
                  <input
                    type="time"
                    value={workHoursStart}
                    onChange={(e) => setWorkHoursStart(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Work End Time</label>
                  <input
                    type="time"
                    value={workHoursEnd}
                    onChange={(e) => setWorkHoursEnd(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-sm"
                  />
                </div>
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={trainingDataOptIn}
                    onChange={(e) => setTrainingDataOptIn(e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded bg-slate-900 border-slate-700"
                  />
                  <div className="text-xs">
                    <span className="font-semibold text-slate-200">Consent for AI Model Improvement (Optional)</span>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      Allow anonymized agent feedback pairs to be recorded in your private training dataset for future custom fine-tuning.
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* STEP 6: Module Selection */}
          {step === 6 && (
            <div className="space-y-4">
              <p className="text-sm text-slate-400">
                Core personal modules remain always active. You can enable or disable optional automation and analytics workspaces:
              </p>

              <div className="space-y-2.5 max-h-80 overflow-y-auto p-1">
                {defaultModulesList.map((mod) => {
                  const isEnabled = enabledModules.includes(mod.key);
                  return (
                    <div
                      key={mod.key}
                      onClick={() => handleToggleModule(mod.key, mod.core)}
                      className={`p-3 rounded-xl border flex items-center justify-between transition cursor-pointer ${
                        isEnabled
                          ? 'bg-indigo-600/15 border-indigo-500/40 text-slate-200'
                          : 'bg-slate-950 border-slate-800 text-slate-500'
                      } ${mod.core ? 'cursor-not-allowed opacity-90' : ''}`}
                    >
                      <div>
                        <div className="text-xs font-semibold flex items-center gap-2">
                          <span>{mod.name}</span>
                          {mod.core && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-mono">
                              CORE
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">{mod.desc}</div>
                      </div>

                      <div
                        className={`w-5 h-5 rounded flex items-center justify-center border ${
                          isEnabled ? 'bg-indigo-600 border-indigo-500 text-white' : 'border-slate-700'
                        }`}
                      >
                        {isEnabled && <Check className="w-3 h-3" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Bottom Action Controls */}
          <div className="flex items-center justify-between pt-6 mt-6 border-t border-slate-800/80">
            {step > 1 ? (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
            ) : (
              <div />
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer disabled:opacity-50"
            >
              {loading
                ? 'Synthesizing LifeSync OS...'
                : step === 6
                ? 'Launch My LifeSync OS'
                : 'Continue'}
              {step < 6 && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
