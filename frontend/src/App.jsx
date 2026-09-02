import { useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [step, setStep] = useState("profile");
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

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

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
      setMessage("Student profile created successfully.");
      setStep("resume");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const uploadResume = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setError("Please select a resume file.");
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
      setMessage("Resume processed successfully.");
      setStep("candidate");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const extraction = resumeResult?.extraction;

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>AI Career Companion</h1>
          <p>Internship Matching & Interview Preparation</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Backend Connected
        </div>
      </header>

      <main className="container">
        <div className="progress">
          <div className={step === "profile" ? "active-step" : ""}>
            <span>1</span>
            Student Profile
          </div>

          <div className={step === "resume" ? "active-step" : ""}>
            <span>2</span>
            Resume Upload
          </div>

          <div className={step === "candidate" ? "active-step" : ""}>
            <span>3</span>
            Candidate Profile
          </div>
        </div>

        {message && <div className="success">{message}</div>}
        {error && <div className="error">{error}</div>}

        {step === "profile" && (
          <section className="card">
            <div className="section-heading">
              <h2>Create Student Profile</h2>
              <p>
                Enter your basic information to create your candidate profile.
              </p>
            </div>

            <form onSubmit={createProfile}>
              <div className="form-grid">
                <div className="field">
                  <label>Full Name *</label>
                  <input
                    name="full_name"
                    value={profile.full_name}
                    onChange={handleProfileChange}
                    placeholder="Enter your full name"
                    required
                  />
                </div>

                <div className="field">
                  <label>Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={profile.email}
                    onChange={handleProfileChange}
                    placeholder="you@example.com"
                    required
                  />
                </div>

                <div className="field">
                  <label>Phone</label>
                  <input
                    name="phone"
                    value={profile.phone}
                    onChange={handleProfileChange}
                    placeholder="+91 XXXXX XXXXX"
                  />
                </div>

                <div className="field">
                  <label>Location</label>
                  <input
                    name="location"
                    value={profile.location}
                    onChange={handleProfileChange}
                    placeholder="Bengaluru, Karnataka"
                  />
                </div>

                <div className="field">
                  <label>Target Role</label>
                  <input
                    name="target_role"
                    value={profile.target_role}
                    onChange={handleProfileChange}
                    placeholder="AI/ML Engineer"
                  />
                </div>

                <div className="field">
                  <label>LinkedIn URL</label>
                  <input
                    name="linkedin_url"
                    value={profile.linkedin_url}
                    onChange={handleProfileChange}
                    placeholder="https://linkedin.com/in/..."
                  />
                </div>
              </div>

              <button className="primary-button" disabled={loading}>
                {loading ? "Creating Profile..." : "Create Student Profile →"}
              </button>
            </form>
          </section>
        )}

        {step === "resume" && (
          <section className="card">
            <div className="section-heading">
              <h2>Upload Your Resume</h2>
              <p>
                Upload your resume and our AI pipeline will extract structured
                candidate information.
              </p>
            </div>

            <div className="profile-created">
              <strong>Profile ID:</strong> {profileId}
              <span>✓ Profile saved successfully</span>
            </div>

            <form onSubmit={uploadResume}>
              <label className="upload-box">
                <div className="upload-icon">↑</div>
                <h3>Select Resume</h3>
                <p>Supported formats: PDF, DOCX, TXT</p>

                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(event) => setSelectedFile(event.target.files[0])}
                />

                {selectedFile && (
                  <div className="selected-file">
                    📄 {selectedFile.name}
                  </div>
                )}
              </label>

              <button
                className="primary-button"
                disabled={loading || !selectedFile}
              >
                {loading ? "Processing Resume..." : "Upload & Analyze Resume →"}
              </button>
            </form>
          </section>
        )}

        {step === "candidate" && extraction && (
          <section>
            <div className="candidate-header">
              <div>
                <h2>Candidate Profile</h2>
                <p>Structured information extracted from your resume.</p>
              </div>

              <div
                className={
                  resumeResult.extraction_method === "gemini_llm"
                    ? "ai-badge"
                    : "fallback-badge"
                }
              >
                {resumeResult.extraction_method === "gemini_llm"
                  ? "🤖 AI Extraction"
                  : "⚙ Local Fallback"}
              </div>
            </div>

            <div className="summary-card">
              <h3>Professional Summary</h3>
              <p>{extraction.summary}</p>
            </div>

            <div className="dashboard-grid">
              <div className="info-card">
                <h3>🛠 Skills</h3>

                <div className="skills">
                  {extraction.skills?.map((skill, index) => (
                    <span key={index}>{skill}</span>
                  ))}
                </div>
              </div>

              <div className="info-card">
                <h3>🎓 Education</h3>

                {extraction.education?.map((item, index) => (
                  <div className="timeline-item" key={index}>
                    <strong>{item.degree}</strong>
                    <p>{item.institution}</p>
                    {item.year && <small>{item.year}</small>}
                  </div>
                ))}
              </div>

              <div className="info-card">
                <h3>💼 Experience</h3>

                {extraction.experience?.length ? (
                  extraction.experience.map((item, index) => (
                    <div className="timeline-item" key={index}>
                      <strong>{item.role}</strong>
                      <p>{item.company}</p>
                      <small>{item.duration}</small>
                    </div>
                  ))
                ) : (
                  <p className="empty">No experience detected.</p>
                )}
              </div>

              <div className="info-card">
                <h3>🚀 Projects</h3>

                {extraction.projects?.map((project, index) => (
                  <div className="project-item" key={index}>
                    <strong>{project.name}</strong>
                    <p>{project.description}</p>

                    <div className="technologies">
                      {project.technologies?.map((tech, techIndex) => (
                        <span key={techIndex}>{tech}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="info-card">
                <h3>📜 Certifications</h3>

                {extraction.certifications?.map((certificate, index) => (
                  <div className="certificate" key={index}>
                    ✓ {certificate}
                  </div>
                ))}
              </div>
            </div>

            <button
              className="secondary-button"
              onClick={() => {
                setStep("resume");
                setResumeResult(null);
              }}
            >
              ← Upload Another Resume
            </button>
          </section>
        )}
      </main>

      <footer>
        AI Career Companion Agent • Milestone 1 Prototype
      </footer>
    </div>
  );
}

export default App;