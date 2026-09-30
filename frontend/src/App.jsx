import { Fragment, useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8001";

const APPLICATION_STATUSES = [
  { value: "Saved", label: "Saved", badgeClass: "badge-gray", icon: "🔖" },
  { value: "Planning to apply", label: "Planning to apply", badgeClass: "badge-blue", icon: "📝" },
  { value: "Applied", label: "Applied", badgeClass: "badge-purple", icon: "🚀" },
  { value: "Application under review", label: "Under Review", badgeClass: "badge-amber", icon: "🔍" },
  { value: "Shortlisted", label: "Shortlisted", badgeClass: "badge-indigo", icon: "⭐" },
  { value: "Interview scheduled", label: "Interview Scheduled", badgeClass: "badge-cyan", icon: "📅" },
  { value: "Interview completed", label: "Interview Completed", badgeClass: "badge-teal", icon: "✅" },
  { value: "Offer received", label: "Offer Received!", badgeClass: "badge-emerald", icon: "🎉" },
  { value: "Rejected", label: "Rejected", badgeClass: "badge-rose", icon: "❌" },
  { value: "Withdrawn", label: "Withdrawn", badgeClass: "badge-slate", icon: "↩" },
];

const NAV_ITEMS = [
  { id: "dashboard", icon: "⌂", label: "Dashboard", group: "WORKSPACE" },
  { id: "profile", icon: "◉", label: "Profile", group: "WORKSPACE" },
  { id: "resume", icon: "▣", label: "Resume", group: "WORKSPACE" },
  { id: "jobs", icon: "✦", label: "Jobs", group: "WORKSPACE" },
  { id: "skillgap", icon: "◇", label: "Skill Gap", group: "GROWTH & PREP" },
  { id: "applications", icon: "✓", label: "Applications", group: "GROWTH & PREP" },
  { id: "interview", icon: "◎", label: "Interview", group: "GROWTH & PREP" },
  { id: "assistant", icon: "✧", label: "Career Assistant", group: "AI COPILOT" },
  { id: "settings", icon: "⚙", label: "Settings", group: "AI COPILOT" },
];

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  const [profileId, setProfileId] = useState(
    localStorage.getItem("career_profile_id") || ""
  );

  const [profile, setProfile] = useState({
    full_name: "",
    email: "",
    phone: "",
    location: "",
    target_role: "",
    linkedin_url: "",
  });

  const [resume, setResume] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [skillGap, setSkillGap] = useState(null);

  // M3 States
  const [tailoredResume, setTailoredResume] = useState(null);
  const [coverLetter, setCoverLetter] = useState(null);
  const [interviewPrep, setInterviewPrep] = useState(null);
  const [mockSession, setMockSession] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatSessionId, setChatSessionId] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // M4.1 Application Tracker States
  const [applications, setApplications] = useState([]);
  const [appDashboard, setAppDashboard] = useState(null);
  const [appLoading, setAppLoading] = useState(false);

  useEffect(() => {
    if (!profileId) return;

    const storageKey = `career_chat_session_${profileId}`;
    const savedSessionId = localStorage.getItem(storageKey);
    const nextSessionId = savedSessionId || `profile_${profileId}_default`;
    localStorage.setItem(storageKey, nextSessionId);
    setChatSessionId(nextSessionId);
    loadProfileData();
  }, [profileId]);

  useEffect(() => {
    if (!profileId || !chatSessionId) return;

    const historyUrl = `/career-assistant/history/${profileId}?conversation_id=${encodeURIComponent(chatSessionId)}`;
    apiRequest(historyUrl)
      .then((historyData) => {
        const sessionMessages = (historyData?.messages || []).map((item) => ({
          role: item.role,
          content: item.content,
          suggested_followups: item.suggested_followups || [],
        }));
        setChatMessages(sessionMessages);
      })
      .catch(() => {
        setChatMessages([]);
      });
  }, [profileId, chatSessionId]);

  async function apiRequest(endpoint, options = {}) {
    const timeoutMs = Number(options.timeoutMs ?? 25000);
    const controller = new AbortController();
    const signal = options.signal || controller.signal;
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        signal,
      });

      let data = null;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail || data?.message || `Request failed (${response.status})`
        );
      }

      return data;
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new Error("The request timed out. Please try again.");
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  async function loadProfileData() {
    try {
      const latestResume = await apiRequest(
        `/profiles/${profileId}/resumes/latest`
      );
      setResume(latestResume);
    } catch {
      setResume(null);
    }

    try {
      const matches = await apiRequest(
        `/profiles/${profileId}/job-matches`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ top_k: 6 }),
        }
      );
      const fetchedJobs = matches.results || [];
      setJobs(fetchedJobs);
      if (fetchedJobs.length > 0 && !selectedJob) {
        setSelectedJob(fetchedJobs[0]);
      }
    } catch {
      setJobs([]);
    }

    loadApplicationsData(profileId);
  }

  async function loadApplicationsData(profId = profileId) {
    if (!profId) return;
    setAppLoading(true);
    try {
      const listData = await apiRequest(`/profiles/${profId}/applications`);
      setApplications(listData?.applications || []);

      const dashData = await apiRequest(`/profiles/${profId}/applications/dashboard`);
      setAppDashboard(dashData || null);
    } catch (err) {
      // ignore
    } finally {
      setAppLoading(false);
    }
  }

  async function trackApplication(job) {
    if (!profileId) {
      setError("Please create or select a profile before tracking applications.");
      setActivePage("profile");
      return;
    }
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const payload = {
        job_id: String(job.job_id || ""),
        company_name: job.company || "Company",
        job_title: job.job_title || "Position",
        job_description: job.job_description || "",
        deadline: job.deadline || "",
        status: "Saved",
      };
      await apiRequest(`/profiles/${profileId}/applications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setMessage(`✓ Tracked "${job.job_title}" at ${job.company} in your applications!`);
      await loadApplicationsData(profileId);
      setActivePage("applications");
    } catch (err) {
      if (err.message?.includes("already exists")) {
        setMessage(`ℹ "${job.job_title}" at ${job.company} is already in your tracker.`);
        await loadApplicationsData(profileId);
        setActivePage("applications");
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function saveApplication(appData, appId = null) {
    if (!profileId) return;
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const endpoint = appId
        ? `/profiles/${profileId}/applications/${appId}`
        : `/profiles/${profileId}/applications`;
      const method = appId ? "PUT" : "POST";
      await apiRequest(endpoint, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(appData),
      });
      setMessage(appId ? "✓ Application updated successfully!" : "✓ New application added successfully!");
      await loadApplicationsData(profileId);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function updateApplicationStatus(appId, newStatus) {
    if (!profileId) return;
    try {
      await apiRequest(`/profiles/${profileId}/applications/${appId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      await loadApplicationsData(profileId);
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteApplication(appId) {
    if (!profileId) return;
    setLoading(true);
    try {
      await apiRequest(`/profiles/${profileId}/applications/${appId}`, {
        method: "DELETE",
      });
      setMessage("✓ Application deleted.");
      await loadApplicationsData(profileId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function startNewChat() {
    if (!profileId) return;

    const nextSessionId = `profile_${profileId}_chat_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
    localStorage.setItem(`career_chat_session_${profileId}`, nextSessionId);
    setChatSessionId(nextSessionId);
    setChatMessages([]);
    setError("");
  }

  async function saveProfile(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await apiRequest("/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });

      const newId = String(data.id);
      setProfileId(newId);
      localStorage.setItem("career_profile_id", newId);
      setMessage("Profile saved successfully.");
      setActivePage("resume");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function uploadResume(event) {
    const file = event.target.files?.[0];
    if (!file || !profileId) return;

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const data = await apiRequest(`/profiles/${profileId}/resumes`, {
        method: "POST",
        body: formData,
      });

      setResume(data);
      setMessage("Resume uploaded and analyzed successfully with AI extraction.");
      await loadProfileData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshMatches() {
    if (!profileId) {
      setActivePage("profile");
      setError("Please create your profile first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await apiRequest(`/profiles/${profileId}/job-matches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ top_k: 6 }),
      });

      setJobs(data.results || []);
      if (data.results?.length > 0) {
        setSelectedJob(data.results[0]);
      }
      setMessage(`${data.results?.length || 0} matching jobs loaded.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function searchJobs(event) {
    event.preventDefault();
    if (!searchQuery.trim()) {
      refreshMatches();
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/jobs/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, top_k: 8 }),
      });

      setJobs(data.results || data.jobs || []);
      setMessage("Search results updated.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // M3 ACTIONS
  // ============================================================

  async function analyzeSkillGap(job) {
    if (!profileId) {
      setActivePage("profile");
      setError("Please create your profile first.");
      return;
    }

    const targetJob = job || selectedJob;
    if (!targetJob) {
      setActivePage("jobs");
      return;
    }

    setSelectedJob(targetJob);
    setActivePage("skillgap");
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/profiles/${profileId}/skill-gap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: targetJob.job_id,
          job_title: targetJob.job_title,
        }),
      });

      setSkillGap(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function generateCustomResume(job) {
    if (!profileId) {
      setActivePage("profile");
      return;
    }

    const targetJob = job || selectedJob;
    if (targetJob) setSelectedJob(targetJob);
    setActivePage("applications");
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/profiles/${profileId}/customize-resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: targetJob?.job_id,
          job_title: targetJob?.job_title,
        }),
      });
      setTailoredResume(data);
      setMessage("Tailored resume generated successfully!");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function generateCoverLetter(job) {
    if (!profileId) {
      setActivePage("profile");
      return;
    }

    const targetJob = job || selectedJob;
    if (targetJob) setSelectedJob(targetJob);
    setActivePage("applications");
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/profiles/${profileId}/cover-letter`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: targetJob?.job_id,
          job_title: targetJob?.job_title,
        }),
      });
      setCoverLetter(data);
      setMessage("Personalized cover letter generated successfully!");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function prepareInterview(job) {
    if (!profileId) {
      setActivePage("profile");
      return;
    }

    const targetJob = job || selectedJob;
    if (targetJob) setSelectedJob(targetJob);
    setActivePage("interview");
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/profiles/${profileId}/interview-prep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: targetJob?.job_id,
          job_title: targetJob?.job_title,
        }),
      });
      setInterviewPrep(data);
      setMessage("Interview question set ready!");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function startMockInterview(job) {
    if (!profileId) {
      setActivePage("profile");
      return;
    }

    const targetJob = job || selectedJob;
    if (targetJob) setSelectedJob(targetJob);
    setActivePage("interview");
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/profiles/${profileId}/mock-interview/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: targetJob?.job_id,
          job_title: targetJob?.job_title,
        }),
      });
      setMockSession(data);
      setMessage("Mock interview session started!");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitMockAnswer(answerText, currentQuestion) {
    if (!mockSession) return;
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/profiles/${profileId}/mock-interview/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interview_id: mockSession.interview_id,
          question_index: mockSession.current_question_index,
          question_text: currentQuestion.question,
          category: currentQuestion.category || "Technical",
          user_answer: answerText,
        }),
      });

      setMockSession((prev) => ({
        ...prev,
        current_question_index: data.next_question_index,
        current_question: data.next_question,
        is_completed: data.is_completed,
        latest_evaluation: data.evaluation,
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function sendChatMessage(messageText) {
    if (!messageText.trim()) return;

    const userTurn = { role: "user", content: messageText };
    setChatMessages((prev) => [...prev, userTurn]);
    setLoading(true);
    setError("");

    try {
      const payload = {
        profile_id: profileId ? Number(profileId) : null,
        job_id: selectedJob?.job_id || null,
        conversation_id: chatSessionId || `profile_${profileId || "guest"}_default`,
        message: messageText,
        history: chatMessages.slice(-6).map((m) => ({
          role: m.role,
          content: m.content,
        })),
      };

      const data = await apiRequest("/career-assistant/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const assistantTurn = {
        role: "assistant",
        content: data.message,
        context_used: data.context_used,
        suggested_followups: data.suggested_followups,
        conversation_id: data.conversation_id,
      };

      setChatMessages((prev) => [...prev, assistantTurn]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function navigate(page) {
    setActivePage(page);
    setSidebarOpen(false);
    setError("");
    setMessage("");

    if (page === "jobs" && profileId && jobs.length === 0) {
      refreshMatches();
    }
  }

  const userName =
    profile?.full_name?.trim() ||
    (profileId ? "Career Explorer" : "Guest User");

  const initials = userName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();

  const skills = useMemo(() => {
    return resume?.extracted_profile?.skills || [];
  }, [resume]);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <span>✦</span>
          </div>

          <div>
            <div className="brand-name">CareerCompanion</div>
            <div className="brand-subtitle">AI CAREER PLATFORM · M3</div>
          </div>
        </div>

        <div className="sidebar-status">
          <span className="status-dot"></span>
          <span>4 Autonomous AI Agents Online</span>
        </div>

        <div className="nav-container">
          {["WORKSPACE", "GROWTH & PREP", "AI COPILOT"].map((group) => (
            <div className="nav-group" key={group}>
              <div className="nav-title">{group}</div>

              {NAV_ITEMS.filter((item) => item.group === group).map((item) => (
                <button
                  key={item.id}
                  className={`nav-item ${
                    activePage === item.id ? "active" : ""
                  }`}
                  onClick={() => navigate(item.id)}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.label}</span>

                  {item.id === "jobs" && jobs.length > 0 && (
                    <span className="nav-badge">{jobs.length}</span>
                  )}
                  {item.id === "skillgap" && selectedJob && (
                    <span className="nav-badge pulse">AI</span>
                  )}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="sidebar-bottom">
          <div className="profile-mini">
            <div className="avatar small">{initials || "U"}</div>

            <div className="profile-mini-text">
              <strong>{userName}</strong>
              <span>{profile?.target_role || "AI Career Explorer"}</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button
            className="mobile-menu"
            onClick={() => setSidebarOpen((value) => !value)}
          >
            ☰
          </button>

          <div className="breadcrumb">
            <span>CareerCompanion</span>
            <span>/</span>
            <strong>{pageTitle(activePage)}</strong>
          </div>

          <div className="topbar-right">
            {selectedJob && (
              <div className="active-job-chip" title="Currently selected target opportunity">
                <span className="chip-dot"></span>
                <span>Target: <strong>{selectedJob.job_title}</strong> ({selectedJob.company})</span>
              </div>
            )}

            <div className="top-status">
              <span className="status-dot"></span>
              M3 Agent Ready
            </div>

            <div className="avatar">{initials || "U"}</div>
          </div>
        </header>

        <div className="content">
          {message && (
            <div className="toast success">
              <span>✓</span>
              {message}
            </div>
          )}

          {error && (
            <div className="toast error">
              <span>!</span>
              {error}
            </div>
          )}

          {activePage === "dashboard" && (
            <Dashboard
              userName={userName}
              profile={profile}
              profileId={profileId}
              jobs={jobs}
              skills={skills}
              resume={resume}
              selectedJob={selectedJob}
              navigate={navigate}
              analyzeSkillGap={analyzeSkillGap}
              generateCustomResume={generateCustomResume}
              generateCoverLetter={generateCoverLetter}
              prepareInterview={prepareInterview}
              startMockInterview={startMockInterview}
              trackApplication={trackApplication}
              refreshMatches={refreshMatches}
              loading={loading}
            />
          )}

          {activePage === "profile" && (
            <ProfilePage
              profile={profile}
              setProfile={setProfile}
              saveProfile={saveProfile}
              loading={loading}
              profileId={profileId}
            />
          )}

          {activePage === "resume" && (
            <ResumePage
              profileId={profileId}
              resume={resume}
              skills={skills}
              uploadResume={uploadResume}
              loading={loading}
              navigate={navigate}
            />
          )}

          {activePage === "jobs" && (
            <JobsPage
              jobs={jobs}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              searchJobs={searchJobs}
              refreshMatches={refreshMatches}
              selectedJob={selectedJob}
              setSelectedJob={setSelectedJob}
              analyzeSkillGap={analyzeSkillGap}
              generateCustomResume={generateCustomResume}
              generateCoverLetter={generateCoverLetter}
              prepareInterview={prepareInterview}
              startMockInterview={startMockInterview}
              trackApplication={trackApplication}
              loading={loading}
            />
          )}

          {activePage === "skillgap" && (
            <SkillGapPage
              jobs={jobs}
              selectedJob={selectedJob}
              setSelectedJob={setSelectedJob}
              skillGap={skillGap}
              analyzeSkillGap={analyzeSkillGap}
              generateCustomResume={generateCustomResume}
              generateCoverLetter={generateCoverLetter}
              prepareInterview={prepareInterview}
              startMockInterview={startMockInterview}
              loading={loading}
              navigate={navigate}
            />
          )}

          {activePage === "applications" && (
            <ApplicationStudioPage
              profileId={profileId}
              jobs={jobs}
              selectedJob={selectedJob}
              setSelectedJob={setSelectedJob}
              tailoredResume={tailoredResume}
              setTailoredResume={setTailoredResume}
              coverLetter={coverLetter}
              setCoverLetter={setCoverLetter}
              generateCustomResume={generateCustomResume}
              generateCoverLetter={generateCoverLetter}
              applications={applications}
              appDashboard={appDashboard}
              appLoading={appLoading}
              loadApplicationsData={loadApplicationsData}
              saveApplication={saveApplication}
              updateApplicationStatus={updateApplicationStatus}
              deleteApplication={deleteApplication}
              loading={loading}
              navigate={navigate}
            />
          )}

          {activePage === "interview" && (
            <InterviewPrepPage
              jobs={jobs}
              selectedJob={selectedJob}
              setSelectedJob={setSelectedJob}
              interviewPrep={interviewPrep}
              prepareInterview={prepareInterview}
              mockSession={mockSession}
              startMockInterview={startMockInterview}
              submitMockAnswer={submitMockAnswer}
              loading={loading}
              navigate={navigate}
            />
          )}

          {activePage === "assistant" && (
            <CareerAssistantPage
              selectedJob={selectedJob}
              profile={profile}
              chatMessages={chatMessages}
              sendChatMessage={sendChatMessage}
              setChatMessages={setChatMessages}
              loading={loading}
              onNewChat={startNewChat}
            />
          )}

          {activePage === "settings" && (
            <SettingsPage
              profile={profile}
              profileId={profileId}
              apiKeyConfigured={true}
            />
          )}
        </div>
      </main>
    </div>
  );
}

// ============================================================
// DASHBOARD
// ============================================================

function Dashboard({
  userName,
  profile,
  profileId,
  jobs,
  skills,
  resume,
  selectedJob,
  navigate,
  analyzeSkillGap,
  generateCustomResume,
  generateCoverLetter,
  prepareInterview,
  startMockInterview,
  trackApplication,
  loading,
}) {
  const topJobs = jobs.slice(0, 3);

  return (
    <div className="page">
      <section className="hero-card">
        <div className="hero-glow glow-one"></div>
        <div className="hero-glow glow-two"></div>

        <div className="hero-content">
          <div className="eyebrow">
            <span>✦</span> CAREER OVERVIEW
          </div>

          <h1>
            Welcome back, {userName}
            <br />
            <span>build your next opportunity.</span>
          </h1>

          <p>
            Here is your career progress and recommended opportunities, organized in one place.
          </p>

          <div className="hero-actions">
            <button
              className="primary-button"
              onClick={() => navigate("jobs")}
            >
              Explore opportunities
              <span>→</span>
            </button>

            <button
              className="secondary-button"
              onClick={() => navigate("assistant")}
            >
              Open career assistant
            </button>
          </div>
        </div>

        <div className="hero-orbit">
          <div className="orbit-ring ring-one"></div>
          <div className="orbit-ring ring-two"></div>
          <div className="orbit-core">✦</div>
          <div className="orbit-dot dot-one">GAP</div>
          <div className="orbit-dot dot-two">CV</div>
          <div className="orbit-dot dot-three">MOCK</div>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          icon="◉"
          label="Profile Strength"
          value={profileId && resume ? "90%" : profileId ? "45%" : "0%"}
          detail={resume ? "Profile & resume verified" : "Upload resume to complete"}
          progress={profileId && resume ? 90 : profileId ? 45 : 0}
        />

        <StatCard
          icon="✦"
          label="Matching Jobs"
          value={jobs.length}
          detail="RAG semantic matches"
          accent
        />

        <StatCard
          icon="◇"
          label="Skills Detected"
          value={skills.length}
          detail="Verified candidate competencies"
        />

        <StatCard
          icon="◎"
          label="AI Agents Ready"
          value="4"
          detail="Gap, Application, Prep, Copilot"
        />
      </section>

      {/* M3 Quick Launchpad */}
      <section className="m3-launchpad">
        <div className="launchpad-header">
          <div>
            <span className="section-kicker">MILESTONE 3 AGENT SUITE</span>
            <h3>What would you like to accomplish today?</h3>
          </div>
        </div>

        <div className="launchpad-grid">
          <div className="launchpad-card" onClick={() => analyzeSkillGap(selectedJob || jobs[0])}>
            <div className="launchpad-icon gap">◇</div>
            <h4>Skill Gap Analysis</h4>
            <p>Compare your profile against requirements, identify critical missing skills & get learning roadmaps.</p>
            <span className="card-link">Launch Agent →</span>
          </div>

          <div className="launchpad-card" onClick={() => generateCustomResume(selectedJob || jobs[0])}>
            <div className="launchpad-icon app">✓</div>
            <h4>Application Studio</h4>
            <p>Generate editable tailored resumes and 6-paragraph cover letters with strict anti-hallucination.</p>
            <span className="card-link">Open Studio →</span>
          </div>

          <div className="launchpad-card" onClick={() => startMockInterview(selectedJob || jobs[0])}>
            <div className="launchpad-icon mock">◎</div>
            <h4>Mock Interview Lab</h4>
            <p>Simulate realistic technical and behavioral interviews with real-time multi-metric AI evaluation.</p>
            <span className="card-link">Start Simulator →</span>
          </div>

          <div className="launchpad-card" onClick={() => navigate("assistant")}>
            <div className="launchpad-icon chat">✧</div>
            <h4>Career Copilot</h4>
            <p>Chat with a context-aware assistant with full knowledge of your profile, jobs, and interview prep.</p>
            <span className="card-link">Chat Now →</span>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel large-panel">
          <div className="panel-header">
            <div>
              <div className="section-kicker">M2 · INTELLIGENT MATCHING</div>
              <h3>Top Career Opportunities</h3>
            </div>

            <button className="text-button" onClick={() => navigate("jobs")}>
              View all ({jobs.length}) →
            </button>
          </div>

          {topJobs.length > 0 ? (
            <div className="mini-jobs">
              {topJobs.map((job) => (
                <MiniJobCard
                  key={job.job_id}
                  job={job}
                  analyzeSkillGap={analyzeSkillGap}
                  generateCustomResume={generateCustomResume}
                  startMockInterview={startMockInterview}
                  trackApplication={trackApplication}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon="✦"
              title="No matches yet"
              text="Create your profile and upload your resume to discover opportunities."
              buttonText="Get Started"
              onClick={() => navigate("profile")}
            />
          )}
        </div>

        <div className="panel insight-panel">
          <div className="panel-header">
            <div>
              <div className="section-kicker">AI INTELLIGENCE</div>
              <h3>Candidate Snapshot</h3>
            </div>
            <span className="sparkle">✦</span>
          </div>

          <div className="insight-main">
            <div className="insight-circle">
              <strong>{skills.length || 0}</strong>
              <span>skills</span>
            </div>

            <div>
              <h4>Structured Profile Grounding</h4>
              <p>
                {skills.length > 0
                  ? `AI agents are actively using your ${skills.length} verified competencies to ground all generation.`
                  : "Upload your resume to unlock personalized AI features."}
              </p>
            </div>
          </div>

          <div className="skill-preview">
            {skills.slice(0, 10).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>

          <button
            className="outline-button full"
            onClick={() => navigate("resume")}
          >
            Manage Resume Intelligence →
          </button>
        </div>
      </section>
    </div>
  );
}

// ============================================================
// PROFILE PAGE
// ============================================================

function ProfilePage({ profile, setProfile, saveProfile, loading, profileId }) {
  function update(field, value) {
    setProfile((current) => ({
      ...current,
      [field]: value,
    }));
  }

  return (
    <div className="page narrow-page">
      <PageIntro
        kicker="PROFILE MANAGEMENT"
        title="Your Career Identity"
        description="Tell CareerCompanion where you are and what target roles you want to pursue."
      />

      <div className="profile-layout">
        <div className="panel profile-form-panel">
          <div className="panel-header">
            <div>
              <div className="section-kicker">PERSONAL INFORMATION</div>
              <h3>Candidate Details</h3>
            </div>

            {profileId && (
              <span className="saved-badge">
                <span>✓</span> Profile ID: #{profileId}
              </span>
            )}
          </div>

          <form onSubmit={saveProfile}>
            <div className="form-grid">
              <Input
                label="Full Name"
                required
                value={profile.full_name}
                onChange={(value) => update("full_name", value)}
                placeholder="Aarav Sharma"
              />

              <Input
                label="Email Address"
                type="email"
                required
                value={profile.email}
                onChange={(value) => update("email", value)}
                placeholder="aarav.sharma@example.com"
              />

              <Input
                label="Phone Number"
                value={profile.phone}
                onChange={(value) => update("phone", value)}
                placeholder="+91 98765 43210"
              />

              <Input
                label="Location"
                value={profile.location}
                onChange={(value) => update("location", value)}
                placeholder="Bengaluru, India"
              />

              <Input
                label="Target Role"
                value={profile.target_role}
                onChange={(value) => update("target_role", value)}
                placeholder="Machine Learning Intern"
              />

              <Input
                label="LinkedIn Profile"
                value={profile.linkedin_url}
                onChange={(value) => update("linkedin_url", value)}
                placeholder="https://linkedin.com/in/..."
              />
            </div>

            <button className="primary-button form-submit" disabled={loading}>
              {loading ? "Saving Profile..." : "Save Career Profile"}
              {!loading && <span>→</span>}
            </button>
          </form>
        </div>

        <div className="profile-side-card">
          <div className="profile-art">
            <div className="profile-art-circle">✦</div>
          </div>

          <div className="section-kicker">ZERO HALLUCINATION</div>
          <h3>Grounded AI Career Advice</h3>

          <p>
            Your verified profile forms the factual anchor for all Milestone 3 agents.
            We strictly forbid AI models from inventing fake metrics or unearned achievements.
          </p>

          <div className="profile-checks">
            <span>✓ Factual skill mapping</span>
            <span>✓ Verified academic projects</span>
            <span>✓ Role-specific customization</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// RESUME PAGE
// ============================================================

function ResumePage({ profileId, resume, skills, uploadResume, loading, navigate }) {
  if (!profileId) {
    return (
      <div className="page narrow-page">
        <PageIntro
          kicker="RESUME INTELLIGENCE"
          title="Upload Your Resume"
          description="Create your profile before uploading your resume."
        />

        <div className="empty-large">
          <div className="empty-icon">▣</div>
          <h3>Create your profile first</h3>
          <p>Your resume will be parsed and connected to your career profile.</p>
          <button className="primary-button" onClick={() => navigate("profile")}>
            Create Profile →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <PageIntro
        kicker="RESUME INTELLIGENCE"
        title="Turn Your Resume into Structured Career Intelligence"
        description="Upload your resume in PDF or DOCX format. Gemini extracts your verified competencies, education, projects, and work experience."
      />

      <div className="resume-grid">
        <div className="upload-card">
          <div className="upload-icon">↑</div>
          <h3>{resume ? "Replace Resume File" : "Upload Candidate Resume"}</h3>
          <p>PDF, DOCX or TXT files supported</p>

          <label className="upload-button">
            {loading ? "Extracting with AI..." : "Choose Resume File"}
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={uploadResume}
              disabled={loading}
            />
          </label>

          {resume && (
            <div className="uploaded-file">
              <span>▣</span>
              <div>
                <strong>{resume.filename || "Uploaded Resume"}</strong>
                <small>
                  {resume.extraction_method === "gemini_llm"
                    ? "✓ Extracted via Gemini LLM"
                    : "✓ Extracted via Local Fallback"}
                </small>
              </div>
              <span className="file-check">✓</span>
            </div>
          )}
        </div>

        <div className="panel extracted-panel">
          <div className="panel-header">
            <div>
              <div className="section-kicker">EXTRACTED PROFILE FACTS</div>
              <h3>Verified Skills Detected</h3>
            </div>
            <span className="skill-count">{skills.length}</span>
          </div>

          {skills.length > 0 ? (
            <div className="large-skill-cloud">
              {skills.map((skill) => (
                <span key={skill} className="skill-badge">{skill}</span>
              ))}
            </div>
          ) : (
            <EmptyState
              icon="◇"
              title="No skills extracted yet"
              text="Upload a resume to populate your verified skill graph."
            />
          )}

          {resume?.extracted_profile?.projects?.length > 0 && (
            <div className="extracted-projects">
              <h4>Extracted Projects</h4>
              <ul>
                {resume.extracted_profile.projects.map((p, idx) => (
                  <li key={idx}>
                    <strong>{typeof p === "string" ? p : p.name}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// JOBS PAGE
// ============================================================

function JobsPage({
  jobs,
  searchQuery,
  setSearchQuery,
  searchJobs,
  refreshMatches,
  selectedJob,
  setSelectedJob,
  analyzeSkillGap,
  generateCustomResume,
  generateCoverLetter,
  prepareInterview,
  startMockInterview,
  loading,
}) {
  return (
    <div className="page">
      <PageIntro
        kicker="M2 · RAG & DETERMINISTIC MATCHING"
        title="Opportunities Ranked for Your Profile"
        description="Jobs are retrieved using 384-dimensional FAISS semantic embeddings and deterministic multi-criteria scoring."
      />

      <div className="jobs-toolbar">
        <form className="search-box" onSubmit={searchJobs}>
          <span>⌕</span>
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search jobs, skills, companies or roles..."
          />
          <button type="submit">Search Jobs</button>
        </form>

        <button
          className="refresh-button"
          onClick={refreshMatches}
          disabled={loading}
        >
          ↻ {loading ? "Loading..." : "Refresh Matching Jobs"}
        </button>
      </div>

      <div className="jobs-heading">
        <div>
          <span className="result-count">{jobs.length}</span>
          <span> curated opportunities</span>
        </div>
        <span className="ranking-note">✦ Hybrid Deterministic & AI Match Scores</span>
      </div>

      {jobs.length > 0 ? (
        <div className="job-list">
          {jobs.map((job, index) => (
            <JobCard
              key={`${job.job_id}-${index}`}
              job={job}
              isSelected={selectedJob?.job_id === job.job_id}
              onSelect={() => setSelectedJob(job)}
              analyzeSkillGap={analyzeSkillGap}
              generateCustomResume={generateCustomResume}
              generateCoverLetter={generateCoverLetter}
              prepareInterview={prepareInterview}
              startMockInterview={startMockInterview}
            />
          ))}
        </div>
      ) : (
        <div className="empty-large">
          <div className="empty-icon">✦</div>
          <h3>No opportunities loaded</h3>
          <p>Create a profile and upload your resume to generate personalized job matches.</p>
        </div>
      )}
    </div>
  );
}

function JobCard({
  job,
  isSelected,
  onSelect,
  analyzeSkillGap,
  generateCustomResume,
  generateCoverLetter,
  prepareInterview,
  startMockInterview,
}) {
  const score = Number(job.match_score || 0);

  return (
    <article className={`job-card ${isSelected ? "selected-job-card" : ""}`}>
      <div className="job-card-top">
        <div className="company-logo large">
          {(job.company || "AI").slice(0, 2).toUpperCase()}
        </div>

        <div className="job-card-title">
          <div className="job-id">{job.job_id}</div>
          <h3>{job.job_title}</h3>
          <strong>{job.company}</strong>
        </div>

        <div className="score-circle">
          <svg viewBox="0 0 80 80">
            <circle className="score-bg" cx="40" cy="40" r="34" />
            <circle
              className="score-progress"
              cx="40"
              cy="40"
              r="34"
              style={{ strokeDasharray: `${score * 2.136} 213.6` }}
            />
          </svg>
          <div>
            <strong>{score}%</strong>
            <span>match</span>
          </div>
        </div>
      </div>

      <div className="job-meta-row">
        <span>⌖ {job.location || "India"}</span>
        <span>◉ {job.work_type || "Remote / Hybrid"}</span>
        {job.retrieval_similarity && (
          <span className="similarity-tag">Similarity: {Math.round(job.retrieval_similarity * 100)}%</span>
        )}
      </div>

      {job.reasoning && (
        <div className="job-reasoning-box">
          <span className="reasoning-label">✦ AI Match Explanation:</span>
          <p>{job.reasoning}</p>
        </div>
      )}

      <div className="skills-section">
        <div className="skill-column">
          <span className="skill-heading matched">MATCHED SKILLS</span>
          <div className="skill-tags">
            {(job.matched_skills || []).length > 0 ? (
              job.matched_skills.map((skill) => (
                <span className="matched-tag" key={skill}>✓ {skill}</span>
              ))
            ) : (
              <span className="muted">No direct matches</span>
            )}
          </div>
        </div>

        {(job.missing_skills || []).length > 0 && (
          <div className="skill-column">
            <span className="skill-heading missing">CRITICAL SKILLS TO DEVELOP</span>
            <div className="skill-tags">
              {job.missing_skills.map((skill) => (
                <span className="missing-tag" key={skill}>+ {skill}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* M3 Action Ribbon */}
      <div className="job-action-ribbon">
        <button
          className="m3-action-btn primary"
          onClick={() => analyzeSkillGap(job)}
          title="Deep dive skill gap analysis"
        >
          ◇ Analyze Gap
        </button>

        <button
          className="m3-action-btn"
          onClick={() => generateCustomResume(job)}
          title="Customize resume for this role"
        >
          ✓ Tailor Resume
        </button>

        <button
          className="m3-action-btn"
          onClick={() => generateCoverLetter(job)}
          title="Draft cover letter"
        >
          ✉ Cover Letter
        </button>

        <button
          className="m3-action-btn"
          onClick={() => prepareInterview(job)}
          title="Interview question bank"
        >
          ◎ Prep Questions
        </button>

        <button
          className="m3-action-btn highlight"
          onClick={() => startMockInterview(job)}
          title="Start AI Mock Interview Simulator"
        >
          ⚡ Mock Simulator
        </button>

        <button
          className="m3-action-btn highlight"
          style={{ background: "linear-gradient(135deg, #3b82f6, #8b5cf6)", color: "#fff" }}
          onClick={() => trackApplication(job)}
          title="Track Application"
        >
          🔖 Track Application
        </button>
      </div>
    </article>
  );
}

// ============================================================
// M3.1 — SKILL GAP ANALYSIS PAGE
// ============================================================

function SkillGapPage({
  jobs,
  selectedJob,
  setSelectedJob,
  skillGap,
  analyzeSkillGap,
  generateCustomResume,
  generateCoverLetter,
  prepareInterview,
  startMockInterview,
  loading,
  navigate,
}) {
  if (!selectedJob && jobs.length === 0) {
    return (
      <div className="page">
        <PageIntro
          kicker="MILESTONE 3.1"
          title="Skill Gap Analysis Agent"
          description="Select a target job opportunity to perform multi-dimensional skill gap evaluation."
        />
        <EmptyState
          icon="◇"
          title="No target job selected"
          text="Explore matching opportunities and select 'Analyze Gap'."
          buttonText="Browse Jobs →"
          onClick={() => navigate("jobs")}
        />
      </div>
    );
  }

  const job = selectedJob || jobs[0];
  const strongMatches = skillGap?.strong_matches || [];
  const criticalGaps = skillGap?.critical_gaps || [];
  const partialGaps = skillGap?.partial_gaps || [];
  const preferredGaps = skillGap?.preferred_gaps || [];
  const recommendations = skillGap?.recommendations || [];
  const matchPercentage = skillGap?.skill_match_percentage ?? job?.match_score ?? 60;

  return (
    <div className="page">
      <div className="skillgap-header">
        <div>
          <button className="back-button" onClick={() => navigate("jobs")}>
            ← Back to Opportunities
          </button>
          <div className="section-kicker">MILESTONE 3.1 · AUTONOMOUS SKILL GAP AGENT</div>
          <h1>Multi-Dimensional Skill Gap Analysis</h1>
          <p>
            Detailed requirement comparison for <strong>{job.job_title}</strong> at <strong>{job.company}</strong>.
          </p>
        </div>

        <div className="big-score">
          <div className="big-score-number">{matchPercentage}%</div>
          <span>Skill Alignment</span>
        </div>
      </div>

      {/* Target Job Selector */}
      {jobs.length > 1 && (
        <div className="job-selector-bar">
          <span>Switch Target Opportunity:</span>
          <select
            value={job.job_id}
            onChange={(e) => {
              const newJob = jobs.find((j) => j.job_id === e.target.value);
              if (newJob) analyzeSkillGap(newJob);
            }}
          >
            {jobs.map((j) => (
              <option key={j.job_id} value={j.job_id}>
                {j.job_title} — {j.company} ({j.match_score}% Match)
              </option>
            ))}
          </select>
        </div>
      )}

      {loading ? (
        <div className="analysis-loading">
          <div className="loader-orbit">✦</div>
          <h3>Skill Gap Agent Analyzing Requirements...</h3>
          <p>Evaluating verified profile competencies against job specifications.</p>
        </div>
      ) : (
        <>
          {skillGap?.summary && (
            <div className="summary-banner">
              <span className="summary-icon">✦</span>
              <div>
                <strong>AI Gap Executive Summary:</strong>
                <p>{skillGap.summary}</p>
              </div>
            </div>
          )}

          <div className="gap-grid">
            {/* Strong Matches */}
            <div className="panel gap-panel">
              <div className="gap-panel-header">
                <div className="gap-panel-icon success">✓</div>
                <div>
                  <span className="section-kicker">VERIFIED STRENGTHS</span>
                  <h3>Strong Matches ({strongMatches.length})</h3>
                </div>
              </div>

              <div className="gap-detail-list">
                {strongMatches.length > 0 ? (
                  strongMatches.map((m, idx) => (
                    <div className="gap-detail-card matched" key={idx}>
                      <div className="gap-card-top">
                        <strong>✓ {m.skill}</strong>
                        <span className="badge success">{m.category || "Required"}</span>
                      </div>
                      <p className="evidence"><em>Evidence:</em> {m.current_evidence}</p>
                      {m.alignment_note && <p className="note">{m.alignment_note}</p>}
                    </div>
                  ))
                ) : (
                  <p className="muted">No direct verified skill matches.</p>
                )}
              </div>
            </div>

            {/* Critical Missing Skills */}
            <div className="panel gap-panel">
              <div className="gap-panel-header">
                <div className="gap-panel-icon danger">⚠</div>
                <div>
                  <span className="section-kicker">CRITICAL GAPS</span>
                  <h3>Missing Required Skills ({criticalGaps.length})</h3>
                </div>
              </div>

              <div className="gap-detail-list">
                {criticalGaps.length > 0 ? (
                  criticalGaps.map((g, idx) => (
                    <div className="gap-detail-card critical" key={idx}>
                      <div className="gap-card-top">
                        <strong>⚠ {g.skill}</strong>
                        <span className="badge danger">Importance: {g.importance || "High"}</span>
                      </div>
                      <p className="why"><strong>Why it matters:</strong> {g.why_it_matters}</p>
                      <p className="evidence"><em>Profile status:</em> {g.current_evidence}</p>
                      <p className="action"><strong>Action:</strong> {g.recommended_action}</p>
                    </div>
                  ))
                ) : (
                  <div className="all-covered">
                    <span>✦</span>
                    <strong>Zero Critical Gaps!</strong>
                    <p>You meet all primary technical requirements for this role.</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Partial & Preferred Skills */}
          {(partialGaps.length > 0 || preferredGaps.length > 0) && (
            <div className="gap-grid secondary">
              {partialGaps.length > 0 && (
                <div className="panel gap-panel">
                  <span className="section-kicker">PARTIAL OVERLAP</span>
                  <h3>Related / Transferable Skills</h3>
                  {partialGaps.map((p, idx) => (
                    <div className="gap-detail-card partial" key={idx}>
                      <strong>◐ {p.skill}</strong>
                      <p>{p.recommended_action}</p>
                    </div>
                  ))}
                </div>
              )}

              {preferredGaps.length > 0 && (
                <div className="panel gap-panel">
                  <span className="section-kicker">BONUS COMPETENCIES</span>
                  <h3>Missing Preferred Skills</h3>
                  {preferredGaps.map((p, idx) => (
                    <div className="gap-detail-card preferred" key={idx}>
                      <strong>+ {p.skill}</strong>
                      <p>{p.recommended_action}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Actionable Learning Roadmap */}
          <div className="roadmap-card">
            <div className="roadmap-title-row">
              <div>
                <span className="section-kicker">STEP-BY-STEP ACTION PLAN</span>
                <h2>How to Close the Gaps & Qualify for this Role</h2>
              </div>
            </div>

            <div className="roadmap-steps-grid">
              {recommendations.length > 0 ? (
                recommendations.map((rec, index) => (
                  <div className="roadmap-item" key={index}>
                    <div className="step-num">{String(rec.priority || index + 1).padStart(2, "0")}</div>
                    <div className="step-body">
                      <h4>{rec.title}</h4>
                      <span className="target-skill-tag">Target: {rec.skill_target}</span>
                      <p>{rec.description}</p>
                      <div className="step-meta">
                        <span>⏱ {rec.estimated_time || "1-2 weeks"}</span>
                        <span>📦 {rec.deliverable || "GitHub Project"}</span>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="roadmap-item">
                  <div className="step-num">01</div>
                  <div className="step-body">
                    <h4>Build an End-to-End Capstone Project</h4>
                    <p>Consolidate your existing strengths in a showcase project deployed live on the web.</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Next Steps M3 Launch Banner */}
          <div className="m3-next-steps-banner">
            <div>
              <h3>Ready to apply for {job.job_title}?</h3>
              <p>Customize your application materials and simulate the technical interview.</p>
            </div>
            <div className="banner-btns">
              <button className="primary-button" onClick={() => generateCustomResume(job)}>
                Tailor Resume →
              </button>
              <button className="secondary-button" onClick={() => generateCoverLetter(job)}>
                Generate Cover Letter
              </button>
              <button className="highlight-button" onClick={() => startMockInterview(job)}>
                Start Mock Interview ⚡
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ============================================================
// M3.2 — APPLICATION STUDIO PAGE (RESUME + COVER LETTER)
// ============================================================

function ApplicationStudioPage({
  profileId,
  jobs,
  selectedJob,
  setSelectedJob,
  tailoredResume,
  setTailoredResume,
  coverLetter,
  setCoverLetter,
  generateCustomResume,
  generateCoverLetter,
  applications = [],
  appDashboard,
  appLoading,
  loadApplicationsData,
  saveApplication,
  updateApplicationStatus,
  deleteApplication,
  loading,
  navigate,
}) {
  const [subTab, setSubTab] = useState("tracker"); // "tracker" | "resume" | "cover_letter"
  const [showModal, setShowModal] = useState(null); // "add" | "edit" | "details" | null
  const [activeApp, setActiveApp] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [deadlineFilter, setDeadlineFilter] = useState("");
  const [appDateFilter, setAppDateFilter] = useState("");

  // Form State for Add / Edit
  const [formData, setFormData] = useState({
    company_name: "",
    job_title: "",
    job_description: "",
    job_id: "",
    status: "Saved",
    application_date: new Date().toISOString().slice(0, 10),
    deadline: "",
    interview_date: "",
    interview_status: "",
    notes: "",
    follow_up_date: "",
  });

  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (profileId && loadApplicationsData) {
      loadApplicationsData(profileId);
    }
  }, [profileId]);

  function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function openAddModal() {
    setFormData({
      company_name: selectedJob?.company || "",
      job_title: selectedJob?.job_title || "",
      job_description: selectedJob?.job_description || "",
      job_id: selectedJob?.job_id ? String(selectedJob.job_id) : "",
      status: "Saved",
      application_date: new Date().toISOString().slice(0, 10),
      deadline: selectedJob?.deadline || "",
      interview_date: "",
      interview_status: "",
      notes: "",
      follow_up_date: "",
    });
    setActiveApp(null);
    setShowModal("add");
  }

  function openEditModal(app) {
    setActiveApp(app);
    setFormData({
      company_name: app.company_name || "",
      job_title: app.job_title || "",
      job_description: app.job_description || "",
      job_id: app.job_id || "",
      status: app.status || "Saved",
      application_date: app.application_date || new Date().toISOString().slice(0, 10),
      deadline: app.deadline || "",
      interview_date: app.interview_date || "",
      interview_status: app.interview_status || "",
      notes: app.notes || "",
      follow_up_date: app.follow_up_date || "",
    });
    setShowModal("edit");
  }

  function openDetailsModal(app) {
    setActiveApp(app);
    setShowModal("details");
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    try {
      await saveApplication(formData, activeApp?.id || null);
      setShowModal(null);
    } catch (err) {
      // error handled in saveApplication
    }
  }

  const filteredApps = useMemo(() => {
    return (applications || []).filter((app) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const comp = (app.company_name || "").toLowerCase();
        const role = (app.job_title || "").toLowerCase();
        const desc = (app.job_description || "").toLowerCase();
        const notes = (app.notes || "").toLowerCase();
        if (!comp.includes(q) && !role.includes(q) && !desc.includes(q) && !notes.includes(q)) {
          return false;
        }
      }
      if (statusFilter && app.status !== statusFilter) {
        return false;
      }
      if (appDateFilter && !(app.application_date || "").startsWith(appDateFilter)) {
        return false;
      }
      if (deadlineFilter) {
        const today = new Date().toISOString().slice(0, 10);
        if (deadlineFilter === "upcoming" && (!app.deadline || app.deadline.slice(0, 10) < today)) {
          return false;
        }
        if (
          deadlineFilter === "overdue" &&
          (!app.deadline || app.deadline.slice(0, 10) >= today || ["Rejected", "Withdrawn", "Offer received"].includes(app.status))
        ) {
          return false;
        }
        if (deadlineFilter === "has_deadline" && !app.deadline) {
          return false;
        }
      }
      return true;
    });
  }, [applications, searchQuery, statusFilter, deadlineFilter, appDateFilter]);

  const metrics = appDashboard?.metrics || {
    total_applications: applications.length,
    active_applications: applications.filter((a) => !["Rejected", "Withdrawn"].includes(a.status)).length,
    upcoming_deadlines: applications.filter((a) => a.deadline && a.deadline >= new Date().toISOString().slice(0, 10)).length,
    interviews_scheduled: applications.filter((a) => a.status === "Interview scheduled" || a.interview_date).length,
    offers_received: applications.filter((a) => a.status === "Offer received").length,
    rejected_applications: applications.filter((a) => a.status === "Rejected").length,
  };

  const currentJob = selectedJob || (jobs.length > 0 ? jobs[0] : null);

  return (
    <div className="page">
      <PageIntro
        kicker="MILESTONE 4.1 · APPLICATION MANAGEMENT MODULE"
        title="Application Tracker & Studio"
        description="Track internship and job applications through their complete lifecycle, monitor deadlines, and customize tailored application materials."
      />

      <div className="studio-tabs">
        <button
          className={`studio-tab ${subTab === "tracker" ? "active" : ""}`}
          onClick={() => setSubTab("tracker")}
        >
          📊 Tracker & Dashboard ({applications.length})
        </button>
        <button
          className={`studio-tab ${subTab === "resume" ? "active" : ""}`}
          onClick={() => setSubTab("resume")}
        >
          📄 Tailored Resume
        </button>
        <button
          className={`studio-tab ${subTab === "cover_letter" ? "active" : ""}`}
          onClick={() => setSubTab("cover_letter")}
        >
          ✉ Personalized Cover Letter
        </button>
      </div>

      {subTab === "tracker" && (
        <div className="studio-section">
          {/* Dashboard Metrics Cards */}
          <div className="app-metrics-grid">
            <div className="app-metric-card">
              <div className="metric-header">
                <span>Total Applications</span>
                <span>📌</span>
              </div>
              <div className="metric-value">{metrics.total_applications}</div>
              <div className="metric-subtext">Saved or submitted</div>
            </div>

            <div className="app-metric-card">
              <div className="metric-header">
                <span>Active Tracked</span>
                <span>🚀</span>
              </div>
              <div className="metric-value" style={{ color: "#93c5fd" }}>
                {metrics.active_applications}
              </div>
              <div className="metric-subtext">In progress</div>
            </div>

            <div className="app-metric-card">
              <div className="metric-header">
                <span>Upcoming Deadlines</span>
                <span>⏰</span>
              </div>
              <div className="metric-value" style={{ color: "#fcd34d" }}>
                {metrics.upcoming_deadlines}
              </div>
              <div className="metric-subtext">Action items</div>
            </div>

            <div className="app-metric-card">
              <div className="metric-header">
                <span>Interviews Scheduled</span>
                <span>📅</span>
              </div>
              <div className="metric-value" style={{ color: "#67e8f9" }}>
                {metrics.interviews_scheduled}
              </div>
              <div className="metric-subtext">Upcoming rounds</div>
            </div>

            <div className="app-metric-card">
              <div className="metric-header">
                <span>Offers Received</span>
                <span>🎉</span>
              </div>
              <div className="metric-value" style={{ color: "#6ee7b7" }}>
                {metrics.offers_received}
              </div>
              <div className="metric-subtext">Congratulations!</div>
            </div>

            <div className="app-metric-card">
              <div className="metric-header">
                <span>Rejected</span>
                <span>❌</span>
              </div>
              <div className="metric-value" style={{ color: "#fda4af" }}>
                {metrics.rejected_applications}
              </div>
              <div className="metric-subtext">Archived</div>
            </div>
          </div>

          {/* Action Header & Search / Filter Toolbar */}
          <div className="tracker-toolbar" style={{ marginTop: "18px" }}>
            <div className="tracker-filters">
              <input
                className="tracker-search-input"
                placeholder="⌕ Search company, role, keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />

              <select
                className="tracker-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses ({applications.length})</option>
                {APPLICATION_STATUSES.map((st) => (
                  <option key={st.value} value={st.value}>
                    {st.icon} {st.label}
                  </option>
                ))}
              </select>

              <select
                className="tracker-select"
                value={deadlineFilter}
                onChange={(e) => setDeadlineFilter(e.target.value)}
              >
                <option value="">All Deadlines</option>
                <option value="upcoming">⏳ Upcoming Deadlines</option>
                <option value="overdue">⚠️ Overdue</option>
                <option value="has_deadline">📅 Has Deadline Set</option>
              </select>

              <input
                type="date"
                className="tracker-select"
                value={appDateFilter}
                onChange={(e) => setAppDateFilter(e.target.value)}
                title="Filter by Application Date"
              />

              {(searchQuery || statusFilter || deadlineFilter || appDateFilter) && (
                <button
                  className="secondary-button"
                  style={{ padding: "6px 12px", fontSize: "12px" }}
                  onClick={() => {
                    setSearchQuery("");
                    setStatusFilter("");
                    setDeadlineFilter("");
                    setAppDateFilter("");
                  }}
                >
                  ✕ Clear Filters
                </button>
              )}
            </div>

            <button className="primary-button" onClick={openAddModal}>
              + Track New Application
            </button>
          </div>

          {/* Quick Glance Widget Cards */}
          {appDashboard?.lists && (
            <div className="quick-glance-grid">
              {(appDashboard.lists.upcoming_deadlines || []).length > 0 && (
                <div className="quick-glance-card">
                  <h4>⏰ Upcoming Application Deadlines</h4>
                  {appDashboard.lists.upcoming_deadlines.map((item) => (
                    <div key={item.id} className="quick-item-row" onClick={() => openDetailsModal(item)} style={{ cursor: "pointer" }}>
                      <div>
                        <strong>{item.job_title}</strong>
                        <span> @ {item.company_name}</span>
                      </div>
                      <span className="deadline-tag upcoming">{item.deadline}</span>
                    </div>
                  ))}
                </div>
              )}

              {(appDashboard.lists.upcoming_interviews || []).length > 0 && (
                <div className="quick-glance-card">
                  <h4>📅 Scheduled Interviews</h4>
                  {appDashboard.lists.upcoming_interviews.map((item) => (
                    <div key={item.id} className="quick-item-row" onClick={() => openDetailsModal(item)} style={{ cursor: "pointer" }}>
                      <div>
                        <strong>{item.job_title}</strong>
                        <span> @ {item.company_name}</span>
                      </div>
                      <span className="deadline-tag upcoming">{item.interview_date ? item.interview_date.slice(0, 10) : "Scheduled"}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Applications Table / Cards */}
          {filteredApps.length > 0 ? (
            <div className="tracker-table-wrapper">
              <table className="tracker-table">
                <thead>
                  <tr>
                    <th>Company & Role</th>
                    <th>Status Workflow</th>
                    <th>Application Date</th>
                    <th>Deadline</th>
                    <th>Interview Schedule</th>
                    <th>Materials</th>
                    <th style={{ textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredApps.map((app) => {
                    const stObj = APPLICATION_STATUSES.find((s) => s.value === app.status) || {
                      badgeClass: "badge-gray",
                      icon: "🔖",
                      label: app.status,
                    };
                    return (
                      <tr key={app.id}>
                        <td>
                          <div className="tracker-app-title">
                            <strong>{app.job_title}</strong>
                            <span>{app.company_name}</span>
                          </div>
                        </td>
                        <td>
                          <select
                            className={`tracker-select app-status-badge ${stObj.badgeClass}`}
                            value={app.status}
                            onChange={(e) => updateApplicationStatus(app.id, e.target.value)}
                            style={{ cursor: "pointer" }}
                          >
                            {APPLICATION_STATUSES.map((st) => (
                              <option key={st.value} value={st.value}>
                                {st.icon} {st.label}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td>{app.application_date || "—"}</td>
                        <td>
                          {app.deadline ? (
                            <span className={`deadline-tag ${app.deadline_status}`}>
                              {app.deadline_status === "overdue" ? "⚠️ Overdue: " : app.deadline_status === "due_today" ? "🔔 Due Today: " : "⏳ "}
                              {app.deadline}
                            </span>
                          ) : (
                            <span className="muted">No deadline</span>
                          )}
                        </td>
                        <td>
                          {app.interview_date ? (
                            <div>
                              <strong>📅 {app.interview_date.slice(0, 10)}</strong>
                              <br />
                              <small className="muted">{app.interview_status || "Interview"}</small>
                            </div>
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </td>
                        <td>
                          <div style={{ display: "flex", gap: "4px" }}>
                            {app.customized_resume && <span title="Tailored Resume Attached">📄</span>}
                            {app.cover_letter && <span title="Cover Letter Attached">✉</span>}
                            {!app.customized_resume && !app.cover_letter && <span className="muted">—</span>}
                          </div>
                        </td>
                        <td style={{ textAlign: "right" }}>
                          <div className="action-btn-group" style={{ justifyContent: "flex-end" }}>
                            <button className="action-icon-btn" onClick={() => openDetailsModal(app)} title="View Details">
                              👁 View
                            </button>
                            <button className="action-icon-btn" onClick={() => openEditModal(app)} title="Edit Application">
                              ✏ Edit
                            </button>
                            <button className="action-icon-btn danger" onClick={() => deleteApplication(app.id)} title="Delete Application">
                              🗑
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-large">
              <div className="empty-icon">📋</div>
              <h3>No applications found</h3>
              <p>
                {applications.length === 0
                  ? "Start tracking your internship applications by adding custom entries or picking from recommended jobs!"
                  : "No applications match your active search filters."}
              </p>
              {applications.length === 0 ? (
                <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                  <button className="primary-button" onClick={openAddModal}>
                    + Track Application Manually
                  </button>
                  <button className="secondary-button" onClick={() => navigate("jobs")}>
                    Explore Recommended Jobs →
                  </button>
                </div>
              ) : (
                <button
                  className="secondary-button"
                  onClick={() => {
                    setSearchQuery("");
                    setStatusFilter("");
                    setDeadlineFilter("");
                    setAppDateFilter("");
                  }}
                >
                  Clear Filters
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* M3.2 Resume Customization Sub-Tab */}
      {subTab === "resume" && (
        <div className="studio-section">
          {currentJob ? (
            <>
              <div className="studio-toolbar">
                <div>
                  <h3>Tailored Resume Representation</h3>
                  <p>Prioritizes relevant skills & projects without inventing ungrounded metrics.</p>
                </div>
                <div className="toolbar-actions">
                  <button className="primary-button" onClick={() => generateCustomResume(currentJob)} disabled={loading}>
                    {loading ? "Generating..." : tailoredResume ? "↻ Regenerate Resume" : "Generate Tailored Resume"}
                  </button>

                  {tailoredResume && (
                    <button
                      className="secondary-button"
                      onClick={() =>
                        copyToClipboard(
                          `${tailoredResume.contact_info?.full_name}\n${tailoredResume.contact_info?.email} | ${tailoredResume.contact_info?.phone}\n\nSUMMARY\n${tailoredResume.professional_summary}\n\nSKILLS\n${tailoredResume.highlighted_skills?.join(", ")}\n\nPROJECTS\n` +
                            tailoredResume.projects
                              ?.map((p) => `${p.title}\n` + p.highlights?.map((h) => `• ${h}`).join("\n"))
                              .join("\n\n")
                        )
                      }
                    >
                      {copied ? "✓ Copied!" : "📋 Copy Formatted Text"}
                    </button>
                  )}
                </div>
              </div>

              {tailoredResume ? (
                <div className="studio-editor-grid">
                  <div className="editor-card">
                    <div className="section-kicker">PROFESSIONAL SUMMARY (EDITABLE)</div>
                    <textarea
                      className="studio-textarea"
                      rows={4}
                      value={tailoredResume.professional_summary || ""}
                      onChange={(e) =>
                        setTailoredResume({
                          ...tailoredResume,
                          professional_summary: e.target.value,
                        })
                      }
                    />

                    <div className="section-kicker" style={{ marginTop: "1rem" }}>
                      HIGHLIGHTED JOB-RELEVANT SKILLS
                    </div>
                    <div className="skill-cloud editable">
                      {(tailoredResume.highlighted_skills || []).map((skill, i) => (
                        <span key={i} className="skill-badge highlighted">
                          ✓ {skill}
                        </span>
                      ))}
                    </div>

                    <div className="section-kicker" style={{ marginTop: "1.5rem" }}>
                      PRIORITIZED PROJECTS
                    </div>
                    {(tailoredResume.projects || []).map((proj, pIdx) => (
                      <div className="editor-project-box" key={pIdx}>
                        <input
                          className="studio-input"
                          value={proj.title}
                          onChange={(e) => {
                            const updated = [...tailoredResume.projects];
                            updated[pIdx].title = e.target.value;
                            setTailoredResume({ ...tailoredResume, projects: updated });
                          }}
                        />
                        <small className="muted">{proj.relevance}</small>
                        <textarea
                          className="studio-textarea compact"
                          rows={3}
                          value={proj.highlights?.join("\n") || ""}
                          onChange={(e) => {
                            const updated = [...tailoredResume.projects];
                            updated[pIdx].highlights = e.target.value.split("\n");
                            setTailoredResume({ ...tailoredResume, projects: updated });
                          }}
                        />
                      </div>
                    ))}
                  </div>

                  <div className="studio-side-panel">
                    <div className="panel">
                      <span className="section-kicker">CUSTOMIZATION STRATEGY</span>
                      <h4>How This Resume Was Tailored</h4>
                      <p>{tailoredResume.customization_strategy}</p>

                      <div className="keyword-bank">
                        <span className="section-kicker">RECOMMENDED KEYWORDS</span>
                        <div className="skill-preview">
                          {(tailoredResume.suggested_keywords || []).map((kw) => (
                            <span key={kw} className="keyword-chip">✦ {kw}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="empty-large">
                  <div className="empty-icon">📄</div>
                  <h3>Generate Tailored Resume</h3>
                  <p>Click below to tailor your resume specifically for {currentJob.job_title}.</p>
                  <button className="primary-button" onClick={() => generateCustomResume(currentJob)} disabled={loading}>
                    {loading ? "Tailoring Resume..." : "Tailor Resume Now →"}
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="empty-large">
              <div className="empty-icon">📄</div>
              <h3>Select a job first</h3>
              <p>Choose a job from Recommended Jobs to tailor your resume.</p>
              <button className="primary-button" onClick={() => navigate("jobs")}>
                Explore Recommended Jobs →
              </button>
            </div>
          )}
        </div>
      )}

      {/* M3.2 Cover Letter Sub-Tab */}
      {subTab === "cover_letter" && (
        <div className="studio-section">
          {currentJob ? (
            <>
              <div className="studio-toolbar">
                <div>
                  <h3>Personalized 6-Paragraph Cover Letter</h3>
                  <p>Structured, professional, and strictly factual based on your real experience.</p>
                </div>
                <div className="toolbar-actions">
                  <button className="primary-button" onClick={() => generateCoverLetter(currentJob)} disabled={loading}>
                    {loading ? "Generating..." : coverLetter ? "↻ Regenerate Cover Letter" : "Generate Cover Letter"}
                  </button>

                  {coverLetter && (
                    <button className="secondary-button" onClick={() => copyToClipboard(coverLetter.full_letter || "")}>
                      {copied ? "✓ Copied!" : "📋 Copy Cover Letter"}
                    </button>
                  )}
                </div>
              </div>

              {coverLetter ? (
                <div className="cover-letter-container">
                  <div className="subject-line-bar">
                    <span>SUBJECT:</span>
                    <input
                      className="studio-input inline"
                      value={coverLetter.subject_line || ""}
                      onChange={(e) => setCoverLetter({ ...coverLetter, subject_line: e.target.value })}
                    />
                  </div>

                  <textarea
                    className="cover-letter-editor"
                    rows={16}
                    value={coverLetter.full_letter || ""}
                    onChange={(e) => setCoverLetter({ ...coverLetter, full_letter: e.target.value })}
                  />
                </div>
              ) : (
                <div className="empty-large">
                  <div className="empty-icon">✉</div>
                  <h3>Draft Professional Cover Letter</h3>
                  <p>Create a customized 6-paragraph cover letter tailored to {currentJob.company}.</p>
                  <button className="primary-button" onClick={() => generateCoverLetter(currentJob)} disabled={loading}>
                    {loading ? "Drafting Cover Letter..." : "Generate Cover Letter Now →"}
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="empty-large">
              <div className="empty-icon">✉</div>
              <h3>Select a job first</h3>
              <p>Choose a job from Recommended Jobs to draft a cover letter.</p>
              <button className="primary-button" onClick={() => navigate("jobs")}>
                Explore Recommended Jobs →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Add / Edit Application Modal */}
      {(showModal === "add" || showModal === "edit") && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>{showModal === "edit" ? "Edit Application" : "Track New Application"}</h3>
              <button className="modal-close-btn" onClick={() => setShowModal(null)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleFormSubmit}>
              <div className="form-grid-2">
                <div className="form-group">
                  <label>Company Name *</label>
                  <input
                    required
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    placeholder="e.g. Google, Microsoft, Startup Inc."
                  />
                </div>

                <div className="form-group">
                  <label>Job Title / Role *</label>
                  <input
                    required
                    value={formData.job_title}
                    onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                    placeholder="e.g. Software Engineering Intern"
                  />
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  >
                    {APPLICATION_STATUSES.map((st) => (
                      <option key={st.value} value={st.value}>
                        {st.icon} {st.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Application Date</label>
                  <input
                    type="date"
                    value={formData.application_date}
                    onChange={(e) => setFormData({ ...formData, application_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label>Application Deadline</label>
                  <input
                    type="date"
                    value={formData.deadline}
                    onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Follow-Up Action Date</label>
                  <input
                    type="date"
                    value={formData.follow_up_date}
                    onChange={(e) => setFormData({ ...formData, follow_up_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label>Interview Date & Time</label>
                  <input
                    type="datetime-local"
                    value={formData.interview_date}
                    onChange={(e) => setFormData({ ...formData, interview_date: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Interview Status / Notes</label>
                  <input
                    value={formData.interview_status}
                    onChange={(e) => setFormData({ ...formData, interview_status: e.target.value })}
                    placeholder="e.g. Technical Round 1 Scheduled"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Job Description (Optional)</label>
                <textarea
                  rows={3}
                  value={formData.job_description}
                  onChange={(e) => setFormData({ ...formData, job_description: e.target.value })}
                  placeholder="Paste job description or requirements summary..."
                />
              </div>

              <div className="form-group">
                <label>Notes & Application Logs</label>
                <textarea
                  rows={3}
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Recruiter contact, referral status, round feedback..."
                />
              </div>

              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setShowModal(null)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={loading}>
                  {loading ? "Saving..." : showModal === "edit" ? "Save Changes" : "Track Application"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Details View Modal */}
      {showModal === "details" && activeApp && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "720px" }}>
            <div className="modal-header">
              <div>
                <h3 style={{ fontSize: "20px" }}>{activeApp.job_title}</h3>
                <span style={{ color: "#94a3b8", fontSize: "14px" }}>{activeApp.company_name}</span>
              </div>
              <button className="modal-close-btn" onClick={() => setShowModal(null)}>
                ✕
              </button>
            </div>

            <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "16px" }}>
              <select
                className={`tracker-select app-status-badge ${
                  APPLICATION_STATUSES.find((s) => s.value === activeApp.status)?.badgeClass || "badge-gray"
                }`}
                value={activeApp.status}
                onChange={(e) => {
                  updateApplicationStatus(activeApp.id, e.target.value);
                  setActiveApp({ ...activeApp, status: e.target.value });
                }}
              >
                {APPLICATION_STATUSES.map((st) => (
                  <option key={st.value} value={st.value}>
                    {st.icon} {st.label}
                  </option>
                ))}
              </select>

              {activeApp.deadline && (
                <span className={`deadline-tag ${activeApp.deadline_status}`}>
                  Deadline: {activeApp.deadline}
                </span>
              )}

              <span style={{ color: "#64748b", fontSize: "12px", marginLeft: "auto" }}>
                Applied: {activeApp.application_date || "N/A"}
              </span>
            </div>

            {activeApp.interview_date && (
              <div className="quick-item-row" style={{ background: "rgba(6, 182, 212, 0.1)", border: "1px solid rgba(6, 182, 212, 0.3)", padding: "10px 14px", marginBottom: "16px" }}>
                <div>
                  <strong style={{ color: "#67e8f9" }}>📅 Scheduled Interview: {activeApp.interview_date}</strong>
                  <div style={{ fontSize: "12px", color: "#cbd5e1" }}>{activeApp.interview_status || "Interview Round"}</div>
                </div>
              </div>
            )}

            {activeApp.job_description && (
              <div className="form-group" style={{ marginBottom: "16px" }}>
                <label>JOB DESCRIPTION</label>
                <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "12px", borderRadius: "8px", fontSize: "13px", color: "#cbd5e1", maxHeight: "150px", overflowY: "auto" }}>
                  {activeApp.job_description}
                </div>
              </div>
            )}

            {activeApp.notes && (
              <div className="form-group" style={{ marginBottom: "16px" }}>
                <label>NOTES & COMMUNICATION HISTORY</label>
                <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "12px", borderRadius: "8px", fontSize: "13px", color: "#cbd5e1", whiteSpace: "pre-wrap" }}>
                  {activeApp.notes}
                </div>
              </div>
            )}

            {/* Generated Application Materials Section */}
            {(activeApp.customized_resume || activeApp.cover_letter) && (
              <div className="panel" style={{ marginTop: "16px" }}>
                <span className="section-kicker">GENERATED APPLICATION MATERIALS</span>
                {activeApp.customized_resume && (
                  <div style={{ marginTop: "8px", padding: "10px", background: "rgba(255, 255, 255, 0.03)", borderRadius: "8px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong>📄 Tailored Resume Available</strong>
                      <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={() => setSubTab("resume")}>
                        View in Studio →
                      </button>
                    </div>
                  </div>
                )}

                {activeApp.cover_letter && (
                  <div style={{ marginTop: "8px", padding: "10px", background: "rgba(255, 255, 255, 0.03)", borderRadius: "8px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong>✉ Tailored Cover Letter Available</strong>
                      <button className="secondary-button" style={{ padding: "4px 10px", fontSize: "12px" }} onClick={() => setSubTab("cover_letter")}>
                        View in Studio →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="modal-footer">
              <button
                className="action-icon-btn danger"
                onClick={() => {
                  deleteApplication(activeApp.id);
                  setShowModal(null);
                }}
              >
                🗑 Delete Application
              </button>
              <button
                className="secondary-button"
                onClick={() => {
                  openEditModal(activeApp);
                }}
              >
                ✏ Edit Application
              </button>
              <button className="primary-button" onClick={() => setShowModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// M3.3 — INTERVIEW PREP & MOCK INTERVIEW LAB PAGE
// ============================================================

function InterviewPrepPage({
  jobs,
  selectedJob,
  setSelectedJob,
  interviewPrep,
  prepareInterview,
  mockSession,
  startMockInterview,
  submitMockAnswer,
  loading,
  navigate,
}) {
  const [subTab, setSubTab] = useState("prep"); // "prep" | "mock"
  const [activeCategory, setActiveCategory] = useState("all");
  const [userAnswerInput, setUserAnswerInput] = useState("");
  const [expandedGuides, setExpandedGuides] = useState({});

  const job = selectedJob || (jobs.length > 0 ? jobs[0] : null);

  function toggleGuide(qId) {
    setExpandedGuides((prev) => ({
      ...prev,
      [qId]: !prev[qId],
    }));
  }

  if (!job) {
    return (
      <div className="page">
        <PageIntro
          kicker="MILESTONE 3.3"
          title="Interview Preparation & Mock Lab"
          description="Prepare with category-specific questions and practice in the interactive AI Interview Lab."
        />
        <EmptyState
          icon="◎"
          title="Select a job first"
          text="Choose an opportunity to generate tailored interview questions."
          buttonText="Explore Jobs →"
          onClick={() => navigate("jobs")}
        />
      </div>
    );
  }

  // Combine all questions for question bank
  const allQuestions = useMemo(() => {
    if (!interviewPrep) return [];
    const list = [];
    (interviewPrep.technical_questions || []).forEach((q) => list.push({ ...q, category: "Technical" }));
    (interviewPrep.project_questions || []).forEach((q) => list.push({ ...q, category: "Projects" }));
    (interviewPrep.resume_questions || []).forEach((q) => list.push({ ...q, category: "Resume" }));
    (interviewPrep.role_specific_questions || []).forEach((q) => list.push({ ...q, category: "Role Specific" }));
    (interviewPrep.hr_questions || []).forEach((q) => list.push({ ...q, category: "HR & Behavioral" }));
    return list;
  }, [interviewPrep]);

  const filteredQuestions = useMemo(() => {
    if (activeCategory === "all") return allQuestions;
    return allQuestions.filter((q) => q.category === activeCategory);
  }, [allQuestions, activeCategory]);

  return (
    <div className="page">
      <PageIntro
        kicker="MILESTONE 3.3 · INTERVIEW AGENT"
        title="Interview Mastery & Interactive Mock Lab"
        description={`Prepare for ${job.job_title} at ${job.company} across technical, architectural, project, and behavioral rubrics.`}
      />

      <div className="studio-tabs">
        <button
          className={`studio-tab ${subTab === "prep" ? "active" : ""}`}
          onClick={() => setSubTab("prep")}
        >
          📚 Question Bank & Prep Guides
        </button>
        <button
          className={`studio-tab ${subTab === "mock" ? "active" : ""}`}
          onClick={() => setSubTab("mock")}
        >
          ⚡ Live Mock Interview Simulator
        </button>
      </div>

      {subTab === "prep" && (
        <div className="interview-prep-section">
          <div className="studio-toolbar">
            <div>
              <h3>Categorized Question Bank</h3>
              <p>Explore questions with preparation frameworks and suggested topics.</p>
            </div>
            <button
              className="primary-button"
              onClick={() => prepareInterview(job)}
              disabled={loading}
            >
              {loading ? "Generating Questions..." : interviewPrep ? "↻ Refresh Question Bank" : "Generate Question Bank"}
            </button>
          </div>

          {interviewPrep ? (
            <>
              {/* Category Filter Pills */}
              <div className="category-filter-row">
                {["all", "Technical", "Projects", "Resume", "Role Specific", "HR & Behavioral"].map((cat) => (
                  <button
                    key={cat}
                    className={`category-pill ${activeCategory === cat ? "active" : ""}`}
                    onClick={() => setActiveCategory(cat)}
                  >
                    {cat === "all" ? "All Questions" : cat}
                  </button>
                ))}
              </div>

              <div className="questions-grid">
                {filteredQuestions.map((q, idx) => {
                  const isExpanded = expandedGuides[q.id || idx];
                  return (
                    <div className="question-card" key={q.id || idx}>
                      <div className="question-card-top">
                        <span className={`badge ${q.category?.toLowerCase().replace(/\s+/g, "-")}`}>
                          {q.category}
                        </span>
                        <button
                          className="practice-btn"
                          onClick={() => {
                            setSubTab("mock");
                            if (!mockSession) startMockInterview(job);
                          }}
                        >
                          Practice in Lab ⚡
                        </button>
                      </div>

                      <h4>"{q.question}"</h4>

                      <button className="expand-guide-btn" onClick={() => toggleGuide(q.id || idx)}>
                        {isExpanded ? "▲ Hide Preparation Guide" : "▼ Show Preparation Guide & Answer Framework"}
                      </button>

                      {isExpanded && (
                        <div className="guide-content">
                          <div className="guide-box">
                            <strong>🎯 Preparation Strategy:</strong>
                            <p>{q.preparation_guide}</p>
                          </div>

                          {q.suggested_topics?.length > 0 && (
                            <div className="topics-box">
                              <strong>Recommended Topics to Mention:</strong>
                              <div className="skill-preview">
                                {q.suggested_topics.map((t, i) => (
                                  <span key={i} className="keyword-chip">{t}</span>
                                ))}
                              </div>
                            </div>
                          )}

                          {q.sample_answer_framework && (
                            <div className="framework-box">
                              <strong>Structured Answer Outline:</strong>
                              <p>{q.sample_answer_framework}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <div className="empty-large">
              <div className="empty-icon">◎</div>
              <h3>Generate Interview Question Bank</h3>
              <p>Click below to generate comprehensive interview questions for {job.job_title}.</p>
              <button
                className="primary-button"
                onClick={() => prepareInterview(job)}
                disabled={loading}
              >
                {loading ? "Generating..." : "Generate Questions Now →"}
              </button>
            </div>
          )}
        </div>
      )}

      {subTab === "mock" && (
        <div className="mock-simulator-section">
          {!mockSession ? (
            <div className="mock-start-card">
              <div className="mock-start-icon">⚡</div>
              <h2>Interactive AI Mock Interview Lab</h2>
              <p>
                Experience a realistic technical interview for <strong>{job.job_title}</strong> at <strong>{job.company}</strong>.
                Submit your answers to receive instant multi-metric evaluation across Technical Understanding, Clarity, Relevance, and Completeness.
              </p>
              <button
                className="primary-button large"
                onClick={() => startMockInterview(job)}
                disabled={loading}
              >
                {loading ? "Initializing Simulator..." : "Launch Mock Interview Simulator →"}
              </button>
            </div>
          ) : (
            <div className="mock-session-view">
              <div className="mock-session-header">
                <div>
                  <span className="section-kicker">SIMULATOR ACTIVE · {job.company}</span>
                  <h3>{job.job_title} Interview</h3>
                </div>

                <div className="session-progress">
                  <span>
                    Question {(mockSession.current_question_index || 0) + 1} of{" "}
                    {mockSession.total_questions || 5}
                  </span>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill"
                      style={{
                        width: `${
                          (((mockSession.current_question_index || 0) + 1) /
                            (mockSession.total_questions || 5)) *
                          100
                        }%`,
                      }}
                    ></div>
                  </div>
                </div>
              </div>

              {mockSession.is_completed ? (
                <div className="mock-completed-card">
                  <div className="mock-complete-icon">✓</div>
                  <h2>Mock Interview Complete!</h2>
                  <p>Great job completing all interview questions for {job.job_title}.</p>
                  <button
                    className="primary-button"
                    onClick={() => startMockInterview(job)}
                  >
                    Start New Mock Session ↻
                  </button>
                </div>
              ) : (
                <div className="active-question-card">
                  <div className="question-banner">
                    <span className="badge technical">
                      {mockSession.current_question?.category || "Technical"}
                    </span>
                    <h3>"{mockSession.current_question?.question}"</h3>
                  </div>

                  <div className="answer-input-zone">
                    <label>Your Spoken / Written Response:</label>
                    <textarea
                      className="mock-answer-textarea"
                      rows={6}
                      value={userAnswerInput}
                      onChange={(e) => setUserAnswerInput(e.target.value)}
                      placeholder="Structure your answer clearly. Mention specific libraries, architecture details, and how you solve problems..."
                    />

                    <div className="answer-actions">
                      <button
                        className="primary-button"
                        onClick={() => {
                          submitMockAnswer(userAnswerInput, mockSession.current_question);
                          setUserAnswerInput("");
                        }}
                        disabled={loading || !userAnswerInput.trim()}
                      >
                        {loading ? "AI Evaluating Answer..." : "Submit Answer for Evaluation →"}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Latest AI Evaluation Feedback */}
              {mockSession.latest_evaluation && (
                <div className="mock-feedback-card">
                  <div className="feedback-header">
                    <div>
                      <span className="section-kicker">AI INTERVIEWER FEEDBACK</span>
                      <h3>Answer Evaluation Report</h3>
                    </div>

                    <div className="overall-score-pill">
                      <strong>{mockSession.latest_evaluation.overall_score || 80}/100</strong>
                      <span>Overall</span>
                    </div>
                  </div>

                  {/* Rubric Score Bars */}
                  <div className="rubric-grid">
                    <RubricBar
                      label="Technical Understanding"
                      score={mockSession.latest_evaluation.technical_understanding?.score || 8}
                      feedback={mockSession.latest_evaluation.technical_understanding?.feedback}
                    />
                    <RubricBar
                      label="Relevance to Question"
                      score={mockSession.latest_evaluation.relevance?.score || 8}
                      feedback={mockSession.latest_evaluation.relevance?.feedback}
                    />
                    <RubricBar
                      label="Clarity & Structure"
                      score={mockSession.latest_evaluation.clarity?.score || 8}
                      feedback={mockSession.latest_evaluation.clarity?.feedback}
                    />
                    <RubricBar
                      label="Completeness"
                      score={mockSession.latest_evaluation.completeness?.score || 7}
                      feedback={mockSession.latest_evaluation.completeness?.feedback}
                    />
                  </div>

                  <div className="feedback-details-grid">
                    <div className="feedback-box success">
                      <strong>✓ What Went Well:</strong>
                      <ul>
                        {(mockSession.latest_evaluation.what_went_well || []).map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="feedback-box warning">
                      <strong>⚠ Areas for Improvement:</strong>
                      <ul>
                        {(mockSession.latest_evaluation.areas_for_improvement || []).map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {mockSession.latest_evaluation.suggested_answer_structure && (
                    <div className="suggested-structure-box">
                      <strong>💡 Model Answer Outline:</strong>
                      <p>{mockSession.latest_evaluation.suggested_answer_structure}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function renderMarkdownContent(content = "") {
  const blocks = (content || "").split(/\n{2,}/).filter(Boolean);

  return (
    <div className="markdown-content">
      {blocks.map((block, index) => {
        if (/^#{1,6}\s+/.test(block.trim())) {
          const match = block.trim().match(/^(#{1,6})\s+(.*)$/);
          const level = match[1].length;
          const text = match[2];
          const HeadingTag = `h${Math.min(level, 4)}`;
          return <HeadingTag key={index}>{renderInlineMarkdown(text)}</HeadingTag>;
        }

        if (/^(?:[-*]|\d+\.)\s+/.test(block.trim())) {
          const items = block
            .split(/\n/)
            .map((line) => line.trim())
            .filter(Boolean)
            .map((line) => line.replace(/^(?:[-*]|\d+\.)\s+/, ""));

          const TagName = /^\d+\./.test(block.trim()) ? "ol" : "ul";
          return (
            <TagName key={index}>
              {items.map((item, itemIndex) => (
                <li key={`${index}-${itemIndex}`}>{renderInlineMarkdown(item)}</li>
              ))}
            </TagName>
          );
        }

        return <p key={index}>{renderInlineMarkdown(block)}</p>;
      })}
    </div>
  );
}

function renderInlineMarkdown(text = "") {
  const segments = text
    .split(/(\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_|`[^`]+`)/g)
    .filter(Boolean);

  return segments.map((segment, index) => {
    if (/^\*\*.*\*\*$/.test(segment)) {
      return <strong key={index}>{segment.slice(2, -2)}</strong>;
    }
    if (/^\*.*\*$/.test(segment)) {
      return <em key={index}>{segment.slice(1, -1)}</em>;
    }
    if (/^_.+_$/.test(segment)) {
      return <em key={index}>{segment.slice(1, -1)}</em>;
    }
    if (/^`.*`$/.test(segment)) {
      return <code key={index}>{segment.slice(1, -1)}</code>;
    }
    return <Fragment key={index}>{segment}</Fragment>;
  });
}

function RubricBar({ label, score, feedback }) {
  const percentage = Math.min(100, (score / 10) * 100);
  return (
    <div className="rubric-item">
      <div className="rubric-top">
        <span>{label}</span>
        <strong>{score}/10</strong>
      </div>
      <div className="rubric-bar-bg">
        <div className="rubric-bar-fill" style={{ width: `${percentage}%` }}></div>
      </div>
      {feedback && <p className="rubric-feedback">{feedback}</p>}
    </div>
  );
}

// ============================================================
// M3.4 — CONVERSATIONAL CAREER ASSISTANT (COPILOT)
// ============================================================

function CareerAssistantPage({
  selectedJob,
  profile,
  chatMessages,
  sendChatMessage,
  setChatMessages,
  loading,
  onNewChat,
}) {
  const [inputText, setInputText] = useState("");

  const suggestedPrompts = [
    "What skills should I learn first for this role?",
    "Why is this internship a strong match for me?",
    "How should I highlight my projects on my resume?",
    "What technical questions might I be asked in this interview?",
    "Compare my strengths against this role's requirements.",
  ];

  function handleSend(textToSend) {
    const text = textToSend || inputText;
    if (!text.trim() || loading) return;
    sendChatMessage(text);
    setInputText("");
  }

  return (
    <div className="page copilot-page">
      <PageIntro
        kicker="MILESTONE 3.4 · CONVERSATIONAL COPILOT"
        title="Career Copilot"
        description="Your intelligent, context-aware career advisor with full access to your profile, target job, skill gaps, and interview prep."
      />

      {selectedJob && (
        <div className="copilot-context-bar">
          <span className="pulse-dot green"></span>
          <span>
            Context Active: <strong>{profile.full_name || "Student"}</strong> applying for{" "}
            <strong>{selectedJob.job_title}</strong> at <strong>{selectedJob.company}</strong>
          </span>
        </div>
      )}

      <div className="copilot-header-row">
        <div className="copilot-header-copy">
          <span className="section-kicker">AI COPILOT</span>
          <h3>Career Copilot</h3>
        </div>
        <button type="button" className="new-chat-button" onClick={onNewChat} disabled={loading}>
          + New Chat
        </button>
      </div>

      <div className="chat-container">
        <div className="chat-thread">
          {chatMessages.length === 0 ? (
            <div className="chat-empty">
              <div className="chat-orbit-icon">✧</div>
              <h3>How can Career Copilot assist you?</h3>
              <p>Ask anything about closing skill gaps, interview strategies, or application materials.</p>
            </div>
          ) : (
            chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`chat-bubble ${msg.role === "user" ? "user-bubble" : "assistant-bubble"}`}
              >
                <div className="bubble-header">
                  <strong>{msg.role === "user" ? "You" : "Career Copilot ✧"}</strong>
                </div>
                <div className="bubble-body">
                  {msg.role === "assistant" ? renderMarkdownContent(msg.content) : msg.content.split("\n").map((line, lIdx) => (
                    <p key={lIdx}>{line}</p>
                  ))}
                </div>

                {msg.suggested_followups?.length > 0 && (
                  <div className="bubble-followups">
                    <span>Suggested follow-ups:</span>
                    <div className="followup-chips">
                      {msg.suggested_followups.map((f, fIdx) => (
                        <button
                          key={fIdx}
                          className="followup-chip"
                          onClick={() => handleSend(f)}
                        >
                          {f} →
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div className="chat-bubble assistant-bubble loading-bubble">
              <span className="dot-typing"></span> Career Copilot is thinking...
            </div>
          )}
        </div>

        {/* Suggested Prompts */}
        <div className="suggested-prompts-row">
          <span>Quick Prompts:</span>
          {suggestedPrompts.map((p, i) => (
            <button
              key={i}
              className="prompt-chip"
              onClick={() => handleSend(p)}
              disabled={loading}
            >
              {p}
            </button>
          ))}
        </div>

        {/* Chat Input Bar */}
        <form
          className="chat-input-bar"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <input
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask anything about your career, skill roadmap, or interview..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !inputText.trim()}>
            Send ✧
          </button>
        </form>
      </div>
    </div>
  );
}

// ============================================================
// SETTINGS PAGE
// ============================================================

function SettingsPage({ profile, profileId, apiKeyConfigured }) {
  return (
    <div className="page narrow-page">
      <PageIntro
        kicker="SETTINGS & CONFIGURATION"
        title="Application Settings"
        description="Configure backend integration, API keys, and environment variables."
      />

      <div className="panel settings-panel">
        <h3>Backend Integration</h3>
        <div className="settings-row">
          <span>API Base URL:</span>
          <code>{API_BASE}</code>
        </div>
        <div className="settings-row">
          <span>Gemini LLM Integration:</span>
          <span className="badge success">Active & Connected</span>
        </div>
        <div className="settings-row">
          <span>FAISS Vector Database:</span>
          <span className="badge success">388 Vectors Indexed</span>
        </div>
        <div className="settings-row">
          <span>Current Active Profile ID:</span>
          <code>{profileId ? `#${profileId}` : "Not Set"}</code>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// SHARED UI COMPONENTS
// ============================================================

function StatCard({ icon, label, value, detail, progress, accent }) {
  return (
    <div className={`stat-card ${accent ? "accent-card" : ""}`}>
      <div className="stat-top">
        <div className="stat-icon">{icon}</div>
        {progress !== undefined && (
          <div className="tiny-progress">
            <div style={{ width: `${progress}%` }}></div>
          </div>
        )}
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-detail">{detail}</div>
    </div>
  );
}

function MiniJobCard({ job, analyzeSkillGap, generateCustomResume, startMockInterview, trackApplication }) {
  return (
    <div className="mini-job">
      <div className="company-logo">
        {(job.company || "AI").slice(0, 2).toUpperCase()}
      </div>

      <div className="mini-job-main">
        <div className="job-title-line">
          <h4>{job.job_title}</h4>
          <span className="match-pill">{job.match_score}%</span>
        </div>
        <p>{job.company}</p>
        <div className="job-meta">
          <span>⌖ {job.location}</span>
          <span>◉ {job.work_type}</span>
        </div>
      </div>

      <div className="mini-actions">
        {trackApplication && (
          <button
            className="mini-action-btn highlight"
            onClick={() => trackApplication(job)}
            title="Track Application"
          >
            🔖
          </button>
        )}
        <button
          className="mini-action-btn"
          onClick={() => analyzeSkillGap(job)}
          title="Analyze Skill Gap"
        >
          ◇
        </button>
        <button
          className="mini-action-btn"
          onClick={() => generateCustomResume(job)}
          title="Tailor Resume"
        >
          ✓
        </button>
        <button
          className="mini-action-btn highlight"
          onClick={() => startMockInterview(job)}
          title="Mock Interview"
        >
          ⚡
        </button>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, placeholder, required, type = "text" }) {
  return (
    <label className="input-group">
      <span>
        {label} {required && <b>*</b>}
      </span>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function PageIntro({ kicker, title, description }) {
  return (
    <div className="page-intro">
      <span className="section-kicker">{kicker}</span>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  );
}

function EmptyState({ icon, title, text, buttonText, onClick }) {
  return (
    <div className="empty-state">
      <div className="empty-small-icon">{icon}</div>
      <h4>{title}</h4>
      <p>{text}</p>
      {buttonText && (
        <button className="primary-button" onClick={onClick}>
          {buttonText}
        </button>
      )}
    </div>
  );
}

function pageTitle(page) {
  const item = NAV_ITEMS.find((nav) => nav.id === page);
  return item?.label || "Dashboard";
}

export default App;