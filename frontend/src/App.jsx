import { useState } from "react";
import "./App.css";

// Backend is running on port 8001
const API_BASE_URL = "http://127.0.0.1:8001";

function App() {
  const [page, setPage] = useState("dashboard");
  const [showOnboarding, setShowOnboarding] = useState(true);

  const [profile, setProfile] = useState({
    full_name: "",
    email: "",
    phone: "",
    location: "",
    target_role: "",
    linkedin_url: "",
  });

  const [profileId, setProfileId] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [resumeResult, setResumeResult] = useState(null);

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const extraction = resumeResult?.extraction;

  // ============================================================
  // PROFILE
  // ============================================================

  const handleProfileChange = (event) => {
    setProfile({
      ...profile,
      [event.target.name]: event.target.value,
    });
  };

  const createProfile = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/profiles`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(profile),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to create profile");
      }

      setProfileId(data.id);
      setMessage("Your career profile has been created.");
      setShowOnboarding(false);
      setPage("resume");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // RESUME UPLOAD
  // ============================================================

  const uploadResume = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setError("Please select a resume file.");
      return;
    }

    if (!profileId) {
      setError("Profile ID is missing. Please create your profile again.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(
        `${API_BASE_URL}/profiles/${profileId}/resumes`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Resume upload failed");
      }

      setResumeResult(data);
      setMessage("Resume analyzed successfully.");
      setPage("resume");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // RAG SEARCH
  // ============================================================

  const searchJobs = async (query) => {
    const response = await fetch(`${API_BASE_URL}/jobs/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        top_k: 10,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to search jobs.");
    }

    return data;
  };

  // ============================================================
  // PERSONALIZED MATCHING
  // ============================================================

  const getRecommendedJobs = async () => {
    if (!profileId) {
      setError("Please create your profile first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/profiles/${profileId}/job-matches`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            top_k: 10,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to load recommended internships."
        );
      }

      const results =
        data.results ||
        data.matches ||
        data.job_matches ||
        data;

      setJobs(Array.isArray(results) ? results : []);
      setPage("jobs");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // TEST RAG
  // ============================================================

  const testJobSearch = async () => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const data = await searchJobs(
        "Python machine learning internship with TensorFlow"
      );

      setJobs(data.results || []);

      setMessage(
        `RAG retrieved ${
          data.result_count || data.results?.length || 0
        } relevant jobs.`
      );

      setPage("jobs");
    } catch (err) {
      setError(`Job search failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // NAVIGATION
  // ============================================================

  const navigate = (target) => {
    setError("");
    setMessage("");
    setPage(target);

    if (target === "jobs") {
      getRecommendedJobs();
    }
  };

  // ============================================================
  // LANDING / ONBOARDING
  // ============================================================

  if (showOnboarding) {
    return (
      <div className="landing-page">
        <div className="landing-background"></div>

        <nav className="landing-nav">
          <div className="brand">
            <div className="brand-icon">✦</div>

            <span>
              Career<span>Companion</span>
            </span>
          </div>

          <div className="landing-nav-right">
            <span>AI-powered career guidance</span>

            <button
              className="nav-login"
              onClick={() => setShowOnboarding(false)}
            >
              Explore Dashboard
            </button>
          </div>
        </nav>

        <main className="hero">
          <div className="hero-content">
            <div className="eyebrow">
              <span>✦</span> AI CAREER COMPANION
            </div>

            <h1>
              Your career.
              <br />
              <span>Powered by AI.</span>
            </h1>

            <p>
              Build your profile, understand your skills, discover the right
              internships, and prepare for interviews — all in one place.
            </p>

            <div className="hero-actions">
              <button
                className="hero-primary"
                onClick={() => {
                  setShowOnboarding(false);
                  setPage("profile");
                }}
              >
                Build My Career Profile →
              </button>

              <button
                className="hero-secondary"
                onClick={() => setShowOnboarding(false)}
              >
                View Dashboard
              </button>
            </div>

            <div className="hero-trust">
              <span>✓ AI Resume Analysis</span>
              <span>✓ Semantic Job Matching</span>
              <span>✓ Personalized Guidance</span>
            </div>
          </div>

          <div className="hero-visual">
            <div className="floating-card profile-preview">
              <div className="preview-top">
                <div className="avatar">AI</div>

                <div>
                  <strong>Career Profile</strong>
                  <small>AI-generated insights</small>
                </div>
              </div>

              <div className="preview-score">
                <div>
                  <small>Profile Strength</small>
                  <strong>87%</strong>
                </div>

                <div className="score-ring">
                  <span>87</span>
                </div>
              </div>

              <div className="preview-tags">
                <span>Python</span>
                <span>Machine Learning</span>
                <span>SQL</span>
                <span>TensorFlow</span>
              </div>
            </div>

            <div className="floating-card match-preview">
              <div className="match-icon">🎯</div>

              <div>
                <small>Best Match</small>
                <strong>AI/ML Intern</strong>
                <span>92% compatible</span>
              </div>
            </div>
          </div>
        </main>

        <div className="landing-features">
          <div>
            <span>01</span>
            <strong>Analyze</strong>
            <p>
              AI extracts your skills and experience from your resume.
            </p>
          </div>

          <div>
            <span>02</span>
            <strong>Match</strong>
            <p>
              Find internships that actually fit your profile.
            </p>
          </div>

          <div>
            <span>03</span>
            <strong>Improve</strong>
            <p>
              Identify skill gaps and prepare for your next interview.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // SIDEBAR
  // ============================================================

  const Sidebar = () => (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">✦</div>

        <div>
          <strong>CareerCompanion</strong>
          <small>AI Career Platform</small>
        </div>
      </div>

      <div className="sidebar-section">
        <span className="sidebar-label">WORKSPACE</span>

        <button
          className={
            page === "dashboard"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("dashboard")}
        >
          <span>⌂</span>
          Dashboard
        </button>

        <button
          className={
            page === "profile"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("profile")}
        >
          <span>◉</span>
          My Profile
        </button>

        <button
          className={
            page === "resume"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("resume")}
        >
          <span>▣</span>
          My Resume
        </button>

        <button
          className={
            page === "jobs"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("jobs")}
        >
          <span>✦</span>
          Recommended Jobs
          <b className="nav-badge">M2</b>
        </button>
      </div>

      <div className="sidebar-section">
        <span className="sidebar-label">GROWTH</span>

        <button
          className={
            page === "skills"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("skills")}
        >
          <span>◇</span>
          Skill Gap
        </button>

        <button
          className={
            page === "interview"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("interview")}
        >
          <span>◎</span>
          Interview Prep
        </button>

        <button
          className={
            page === "applications"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("applications")}
        >
          <span>✓</span>
          Applications
        </button>
      </div>

      <div className="sidebar-section">
        <span className="sidebar-label">ASSISTANCE</span>

        <button
          className={
            page === "assistant"
              ? "side-item active"
              : "side-item"
          }
          onClick={() => navigate("assistant")}
        >
          <span>✧</span>
          Career Assistant
        </button>
      </div>

      <div className="sidebar-bottom">
        <button className="side-item">
          <span>⚙</span>
          Settings
        </button>

        <div className="user-mini">
          <div className="user-avatar">
            {profile.full_name
              ? profile.full_name.charAt(0).toUpperCase()
              : "S"}
          </div>

          <div>
            <strong>{profile.full_name || "Student"}</strong>
            <small>
              {profile.target_role || "Career Explorer"}
            </small>
          </div>
        </div>
      </div>
    </aside>
  );

  // ============================================================
  // TOPBAR
  // ============================================================

  const Topbar = () => (
    <header className="topbar">
      <div>
        <span className="breadcrumb">Career Companion</span>

        <h2>
          {page === "dashboard" && "Dashboard"}
          {page === "profile" && "My Profile"}
          {page === "resume" && "My Resume"}
          {page === "jobs" && "Recommended Internships"}
          {page === "skills" && "Skill Gap Analysis"}
          {page === "interview" && "Interview Preparation"}
          {page === "applications" && "Applications"}
          {page === "assistant" && "Career Assistant"}
        </h2>
      </div>

      <div className="topbar-right">
        <div className="connection">
          <span></span>
          AI Engine Online
        </div>

        <div className="topbar-avatar">
          {profile.full_name
            ? profile.full_name.charAt(0).toUpperCase()
            : "S"}
        </div>
      </div>
    </header>
  );

  // ============================================================
  // DASHBOARD
  // ============================================================

  const Dashboard = () => (
    <div className="page-content">
      <section className="welcome-banner">
        <div>
          <div className="welcome-eyebrow">
            WELCOME BACK
          </div>

          <h1>
            {profile.full_name
              ? `Hi, ${profile.full_name.split(" ")[0]} 👋`
              : "Build your career with confidence."}
          </h1>

          <p>
            Your AI-powered career workspace is ready. Start by completing
            your profile and uploading your resume.
          </p>

          <button
            className="dashboard-primary"
            onClick={() =>
              navigate(profileId ? "resume" : "profile")
            }
          >
            {profileId
              ? "Manage My Resume →"
              : "Create My Profile →"}
          </button>
        </div>

        <div className="banner-orbit">
          <div className="orbit-center">✦</div>
          <div className="orbit-dot dot-one">AI</div>
          <div className="orbit-dot dot-two">CV</div>
          <div className="orbit-dot dot-three">🎯</div>
        </div>
      </section>

      <div className="dashboard-heading">
        <div>
          <h2>Your Career Overview</h2>
          <p>
            Everything you need to move toward your next opportunity.
          </p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon purple">◉</div>

          <div>
            <small>PROFILE STATUS</small>
            <strong>
              {profileId ? "Complete" : "Not Started"}
            </strong>

            <span>
              {profileId
                ? "✓ Profile created"
                : "Create your profile"}
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon blue">▣</div>

          <div>
            <small>RESUME STATUS</small>

            <strong>
              {resumeResult ? "Analyzed" : "Pending"}
            </strong>

            <span>
              {resumeResult
                ? "✓ AI analysis complete"
                : "Upload your resume"}
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">✦</div>

          <div>
            <small>JOB MATCHING</small>

            <strong>{jobs.length || "—"}</strong>

            <span>
              Recommended opportunities
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">◇</div>

          <div>
            <small>SKILLS DETECTED</small>

            <strong>
              {extraction?.skills?.length || "—"}
            </strong>

            <span>From your resume</span>
          </div>
        </div>
      </div>

      <div className="dashboard-columns">
        <div className="dashboard-panel">
          <div className="panel-heading">
            <div>
              <h3>Career Journey</h3>
              <p>
                Complete these steps to unlock your AI career tools.
              </p>
            </div>
          </div>

          <div className="journey">
            <div
              className={
                profileId
                  ? "journey-step done"
                  : "journey-step"
              }
            >
              <div className="journey-number">
                {profileId ? "✓" : "1"}
              </div>

              <div>
                <strong>Create your profile</strong>
                <p>Add your basic career information.</p>
              </div>
            </div>

            <div
              className={
                resumeResult
                  ? "journey-step done"
                  : "journey-step"
              }
            >
              <div className="journey-number">
                {resumeResult ? "✓" : "2"}
              </div>

              <div>
                <strong>Analyze your resume</strong>
                <p>
                  Let AI understand your experience and skills.
                </p>
              </div>
            </div>

            <div className="journey-step">
              <div className="journey-number">3</div>

              <div>
                <strong>Discover internships</strong>
                <p>
                  Get personalized job recommendations.
                </p>
              </div>
            </div>

            <div className="journey-step">
              <div className="journey-number">4</div>

              <div>
                <strong>Prepare & improve</strong>
                <p>
                  Close skill gaps and practice interviews.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="dashboard-panel ai-insight">
          <div className="panel-heading">
            <div>
              <h3>AI Career Insight</h3>
              <p>
                Your intelligent career assistant.
              </p>
            </div>

            <span className="sparkle">✦</span>
          </div>

          <div className="insight-body">
            <div className="insight-avatar">AI</div>

            <p>
              {resumeResult
                ? "Your resume has been analyzed. Explore your extracted skills and discover internships matched to your profile."
                : "Upload your resume and I’ll analyze your skills, projects, education, and experience to personalize your career journey."}
            </p>

            <button
              className="insight-button"
              onClick={() =>
                navigate(
                  resumeResult ? "jobs" : "resume"
                )
              }
            >
              {resumeResult
                ? "Find My Matches →"
                : "Analyze My Resume →"}
            </button>
          </div>
        </div>
      </div>

      <div className="feature-strip">
        <div>
          <span>✦</span>
          <strong>AI Resume Analysis</strong>
          <p>Structured candidate profile extraction</p>
        </div>

        <div>
          <span>⌕</span>
          <strong>Semantic Job Search</strong>
          <p>RAG-powered internship retrieval</p>
        </div>

        <div>
          <span>🎯</span>
          <strong>Smart Matching</strong>
          <p>Personalized job compatibility scoring</p>
        </div>
      </div>
    </div>
  );

  // ============================================================
  // PROFILE PAGE
  // ============================================================

  const ProfilePage = () => (
    <div className="page-content">
      <div className="page-intro">
        <div>
          <span className="eyebrow-small">PROFILE</span>

          <h1>Tell us about yourself</h1>

          <p>
            Your profile helps Career Companion personalize internship
            recommendations and career guidance.
          </p>
        </div>
      </div>

      <section className="form-card">
        <form onSubmit={createProfile}>
          <div className="form-section-title">
            <span>01</span>

            <div>
              <h3>Personal Information</h3>
              <p>Basic information about you.</p>
            </div>
          </div>

          <div className="modern-form-grid">
            <div className="modern-field">
              <label>Full Name *</label>

              <input
                name="full_name"
                value={profile.full_name}
                onChange={handleProfileChange}
                placeholder="e.g. Bibi Fatima Yadwad"
                required
              />
            </div>

            <div className="modern-field">
              <label>Email Address *</label>

              <input
                type="email"
                name="email"
                value={profile.email}
                onChange={handleProfileChange}
                placeholder="you@example.com"
                required
              />
            </div>

            <div className="modern-field">
              <label>Phone Number</label>

              <input
                name="phone"
                value={profile.phone}
                onChange={handleProfileChange}
                placeholder="+91 XXXXX XXXXX"
              />
            </div>

            <div className="modern-field">
              <label>Location</label>

              <input
                name="location"
                value={profile.location}
                onChange={handleProfileChange}
                placeholder="Bengaluru, Karnataka"
              />
            </div>
          </div>

          <div className="form-section-title second">
            <span>02</span>

            <div>
              <h3>Career Preferences</h3>
              <p>
                Tell us what kind of opportunity you want.
              </p>
            </div>
          </div>

          <div className="modern-form-grid">
            <div className="modern-field">
              <label>Target Role</label>

              <input
                name="target_role"
                value={profile.target_role}
                onChange={handleProfileChange}
                placeholder="e.g. AI/ML Engineer"
              />
            </div>

            <div className="modern-field">
              <label>LinkedIn Profile</label>

              <input
                type="url"
                name="linkedin_url"
                value={profile.linkedin_url}
                onChange={handleProfileChange}
                placeholder="https://linkedin.com/in/..."
              />
            </div>
          </div>

          <button
            type="submit"
            className="dashboard-primary"
            disabled={loading}
          >
            {loading
              ? "Saving Profile..."
              : "Save Profile →"}
          </button>
        </form>
      </section>
    </div>
  );

  // ============================================================
  // RESUME PAGE
  // ============================================================

  const ResumePage = () => (
    <div className="page-content">
      <div className="page-intro">
        <div>
          <span className="eyebrow-small">
            RESUME INTELLIGENCE
          </span>

          <h1>My Resume</h1>

          <p>
            Upload your resume and let AI transform it into a structured
            career profile.
          </p>
        </div>

        {resumeResult && (
          <div
              className={
              resumeResult.extraction_method === "gemini"
              ? "ai-status"
              : "fallback-status"
              }
          >
            {resumeResult.extraction_method === "gemini"
            ? "✦ Gemini AI Analysis"
            : "⚙ Local Analysis"}
          </div>
        )}
      </div>

      {!profileId && (
        <div className="notice-card">
          <span>!</span>

          <div>
            <strong>Create your profile first</strong>

            <p>
              A student profile is required before a resume can be
              uploaded.
            </p>
          </div>

          <button onClick={() => navigate("profile")}>
            Create Profile →
          </button>
        </div>
      )}

      {profileId && (
        <>
          <section className="resume-upload-card">
            <div className="upload-visual">
              <div className="document-icon">▤</div>

              <div>
                <h3>Upload your latest resume</h3>

                <p>
                  PDF, DOCX or TXT · Your file stays in your local backend.
                </p>
              </div>
            </div>

            <form onSubmit={uploadResume}>
              <label className="modern-upload">
                <div className="upload-cloud">↑</div>

                <strong>
                  {selectedFile
                    ? selectedFile.name
                    : "Choose a resume file"}
                </strong>

                <span>
                  {selectedFile
                    ? "Ready to analyze"
                    : "Drag & drop or browse from your computer"}
                </span>

                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(event) => {
                    setSelectedFile(
                      event.target.files?.[0] || null
                    );
                  }}
                />
              </label>

              <button
                type="submit"
                className="dashboard-primary"
                disabled={loading || !selectedFile}
              >
                {loading
                  ? "AI is analyzing..."
                  : "Upload & Analyze Resume →"}
              </button>
            </form>
          </section>

          {extraction && (
            <section className="resume-analysis">
              <div className="analysis-header">
                <div>
                  <span className="eyebrow-small">
                    AI EXTRACTION
                  </span>

                  <h2>Your Candidate Profile</h2>
                </div>

                <span className="analysis-complete">
                  ✓ Complete
                </span>
              </div>

              <div className="summary-highlight">
                <div className="summary-symbol">✦</div>

                <div>
                  <small>PROFESSIONAL SUMMARY</small>

                  <p>
                    {extraction.summary ||
                      "No summary detected."}
                  </p>
                </div>
              </div>

              <div className="analysis-grid">
                <div className="analysis-card">
                  <h3>🛠 Skills</h3>

                  <div className="skill-cloud">
                    {extraction.skills?.length ? (
                      extraction.skills.map(
                        (skill, index) => (
                          <span key={index}>{skill}</span>
                        )
                      )
                    ) : (
                      <p className="empty">
                        No skills detected.
                      </p>
                    )}
                  </div>
                </div>

                <div className="analysis-card">
                  <h3>🎓 Education</h3>

                  {extraction.education?.length ? (
                    extraction.education.map(
                      (item, index) => (
                        <div
                          className="analysis-item"
                          key={index}
                        >
                          <strong>
                            {item.degree || "Education"}
                          </strong>

                          <p>
                            {item.institution || ""}
                          </p>

                          {item.year && (
                            <small>{item.year}</small>
                          )}
                        </div>
                      )
                    )
                  ) : (
                    <p className="empty">
                      No education detected.
                    </p>
                  )}
                </div>

                <div className="analysis-card">
                  <h3>💼 Experience</h3>

                  {extraction.experience?.length ? (
                    extraction.experience.map(
                      (item, index) => (
                        <div
                          className="analysis-item"
                          key={index}
                        >
                          <strong>
                            {item.role || "Experience"}
                          </strong>

                          <p>
                            {item.company || ""}
                          </p>

                          {item.duration && (
                            <small>
                              {item.duration}
                            </small>
                          )}
                        </div>
                      )
                    )
                  ) : (
                    <p className="empty">
                      No experience detected.
                    </p>
                  )}
                </div>

                <div className="analysis-card">
                  <h3>🚀 Projects</h3>

                  {extraction.projects?.length ? (
                    extraction.projects.map(
                      (project, index) => (
                        <div
                          className="analysis-item"
                          key={index}
                        >
                          <strong>
                            {project.name || "Project"}
                          </strong>

                          <p>
                            {project.description || ""}
                          </p>

                          <div className="mini-tags">
                            {project.technologies?.map(
                              (tech, techIndex) => (
                                <span key={techIndex}>
                                  {tech}
                                </span>
                              )
                            )}
                          </div>
                        </div>
                      )
                    )
                  ) : (
                    <p className="empty">
                      No projects detected.
                    </p>
                  )}
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );

  // ============================================================
  // JOBS PAGE
  // ============================================================

  const JobsPage = () => (
    <div className="page-content">
      <div className="page-intro jobs-intro">
        <div>
          <span className="eyebrow-small">
            M2 · INTELLIGENT MATCHING
          </span>

          <h1>Recommended Internships</h1>

          <p>
            Opportunities retrieved and ranked using your profile, skills,
            target role, and semantic job similarity.
          </p>
        </div>

        <button
          className="dashboard-primary"
          onClick={getRecommendedJobs}
          disabled={loading}
        >
          {loading
            ? "Finding Matches..."
            : "Refresh Matches ↻"}
        </button>
      </div>

      {!profileId && (
        <div className="notice-card">
          <span>!</span>

          <div>
            <strong>Create your student profile</strong>

            <p>
              Personalized matching needs your profile and resume data.
            </p>
          </div>

          <button onClick={() => navigate("profile")}>
            Get Started →
          </button>
        </div>
      )}

      {profileId && !resumeResult && (
        <div className="empty-state-large">
          <div>▤</div>

          <h2>Upload your resume first</h2>

          <p>
            Career Companion needs your skills and experience to calculate
            personalized internship matches.
          </p>

          <button
            className="dashboard-primary"
            onClick={() => navigate("resume")}
          >
            Upload Resume →
          </button>
        </div>
      )}

      {jobs.length > 0 && (
        <div className="jobs-list">
          <div className="results-header">
            <div>
              <strong>
                {jobs.length} opportunities
              </strong>

              <span>
                ranked for your profile
              </span>
            </div>

            <div className="powered-badge">
              ✦ AI MATCHING
            </div>
          </div>

          {jobs.map((job, index) => {
            const score = Number(
              job.match_score ??
                job.score ??
                job.match_percentage ??
                0
            );

            const title =
              job.job_title ||
              job.title ||
              job.job_role ||
              "Internship Opportunity";

            const company =
              job.company ||
              job.company_name ||
              "Company";

            const location =
              job.location ||
              job.job_location ||
              "Location not specified";

            const matchedSkills =
              job.matched_skills ||
              job.matching_skills ||
              [];

            const missingSkills =
              job.missing_skills ||
              job.skill_gaps ||
              [];

            return (
              <div
                className="job-card"
                key={index}
              >
                <div className="job-rank">
                  {index + 1}
                </div>

                <div className="company-logo">
                  {company.charAt(0).toUpperCase()}
                </div>

                <div className="job-main">
                  <div className="job-title-row">
                    <div>
                      <h3>{title}</h3>
                      <p>{company}</p>
                    </div>

                    <div className="match-score">
                      <strong>
                        {score.toFixed(0)}%
                      </strong>

                      <span>Match</span>
                    </div>
                  </div>

                  <div className="job-meta">
                    <span>⌖ {location}</span>

                    <span>
                      ◷ Internship / Early Career
                    </span>
                  </div>

                  {matchedSkills.length > 0 && (
                    <div className="job-skills">
                      <small>MATCHED SKILLS</small>

                      <div>
                        {matchedSkills
                          .slice(0, 5)
                          .map((skill, i) => (
                            <span
                              className="matched"
                              key={i}
                            >
                              ✓ {skill}
                            </span>
                          ))}
                      </div>
                    </div>
                  )}

                  {missingSkills.length > 0 && (
                    <div className="job-skills">
                      <small>SKILL GAPS</small>

                      <div>
                        {missingSkills
                          .slice(0, 4)
                          .map((skill, i) => (
                            <span
                              className="missing"
                              key={i}
                            >
                              + {skill}
                            </span>
                          ))}
                      </div>
                    </div>
                  )}

                  {job.reasoning && (
                    <div className="why-match">
                      <strong>
                        ✦ Why this match?
                      </strong>

                      <p>{job.reasoning}</p>
                    </div>
                  )}
                </div>

                <button className="job-apply">
                  View Role →
                </button>
              </div>
            );
          })}
        </div>
      )}

      {profileId &&
        resumeResult &&
        jobs.length === 0 &&
        !loading && (
          <div className="empty-state-large">
            <div>🎯</div>

            <h2>
              No recommendations loaded yet
            </h2>

            <p>
              Click refresh to run the personalized matching engine.
            </p>

            <button
              className="dashboard-primary"
              onClick={getRecommendedJobs}
            >
              Find My Matches →
            </button>
          </div>
        )}
    </div>
  );

  // ============================================================
  // PLACEHOLDER GROWTH PAGES
  // ============================================================

  const FeaturePage = ({ type }) => {
    const content = {
      skills: {
        icon: "◇",
        label: "SKILL INTELLIGENCE",
        title: "Skill Gap Analysis",
        description:
          "Understand which skills you already have and which skills will improve your chances of landing your target roles.",
        features: [
          "Compare your skills against internship requirements",
          "Identify high-priority missing skills",
          "Get personalized learning recommendations",
        ],
      },

      interview: {
        icon: "◎",
        label: "INTERVIEW INTELLIGENCE",
        title: "Interview Preparation",
        description:
          "Practice technical and behavioral interviews with an AI career coach.",
        features: [
          "Role-specific interview questions",
          "AI-generated feedback",
          "Technical and behavioral preparation",
        ],
      },

      applications: {
        icon: "✓",
        label: "APPLICATION TRACKER",
        title: "Applications",
        description:
          "Keep your internship applications organized from discovery to offer.",
        features: [
          "Track applications and statuses",
          "Save promising internship opportunities",
          "Never lose track of a deadline",
        ],
      },

      assistant: {
        icon: "✧",
        label: "AI CAREER ASSISTANT",
        title: "Your Career Assistant",
        description:
          "Ask questions about your resume, career direction, internships, skills, and interview preparation.",
        features: [
          "Ask career-related questions",
          "Get personalized resume suggestions",
          "Plan your next career step",
        ],
      },
    };

    const data = content[type];

    return (
      <div className="page-content">
        <div className="coming-hero">
          <div className="coming-icon">
            {data.icon}
          </div>

          <span className="eyebrow-small">
            {data.label}
          </span>

          <h1>{data.title}</h1>

          <p>{data.description}</p>

          <div className="coming-status">
            <span>●</span>
            Coming in the next milestone
          </div>
        </div>

        <div className="planned-grid">
          {data.features.map(
            (feature, index) => (
              <div
                className="planned-card"
                key={index}
              >
                <span>
                  0{index + 1}
                </span>

                <strong>{feature}</strong>

                <p>
                  This capability will be connected to your personalized
                  career intelligence layer.
                </p>
              </div>
            )
          )}
        </div>
      </div>
    );
  };

  // ============================================================
  // MAIN APPLICATION
  // ============================================================

  return (
    <div className="platform">
      <Sidebar />

      <div className="main-area">
        <Topbar />

        {message && (
          <div className="global-message success">
            ✓ {message}
          </div>
        )}

        {error && (
          <div className="global-message error">
            ! {error}
          </div>
        )}

        {page === "dashboard" && <Dashboard />}

        {page === "profile" && <ProfilePage />}

        {page === "resume" && <ResumePage />}

        {page === "jobs" && <JobsPage />}

        {page === "skills" && (
          <FeaturePage type="skills" />
        )}

        {page === "interview" && (
          <FeaturePage type="interview" />
        )}

        {page === "applications" && (
          <FeaturePage type="applications" />
        )}

        {page === "assistant" && (
          <FeaturePage type="assistant" />
        )}

        <footer className="platform-footer">
          <span>AI Career Companion</span>
          <span>Milestone 2 Prototype</span>
          <span>
            RAG • AI Matching • Resume Intelligence
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;