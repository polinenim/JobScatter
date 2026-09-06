"use client";

import React, { FormEvent, useState } from "react";

type Profile = {
  education: string;
  skills: string;
  capabilities: string;
  experience: string;
  languages: string;
  targetRoles: string;
  location: string;
  workPreferences: string;
  certifications: string;
  projects: string;
};

type SearchResult = {
  company_name: string;
  job_title: string;
  posted_at: string;
  job_link: string;
};

const defaultCandidateId = "32f7bcbf-2e87-4b9b-8847-beb47d4defdf";

const emptyProfile: Profile = {
  education: "M.Sc. Information Technology",
  skills: "Python, SQL, Git",
  capabilities: "Software development, Data analysis",
  experience: "Early-career technology profile",
  languages: "English",
  targetRoles: "AI / ML, Software, Data",
  location: "Finland",
  workPreferences: "Internship, Trainee, Graduate, Junior",
  certifications: "",
  projects: "",
};

const profileFields: Array<{ key: keyof Profile; label: string; hint: string }> = [
  { key: "education", label: "Education", hint: "Degrees, institutions, or relevant study" },
  { key: "skills", label: "Skills", hint: "Technical skills, tools, and technologies" },
  { key: "capabilities", label: "Capabilities", hint: "Broader strengths and ways of working" },
  { key: "experience", label: "Experience", hint: "Roles, organizations, and experience details" },
  { key: "languages", label: "Languages", hint: "Languages and proficiency" },
  { key: "targetRoles", label: "Target Roles", hint: "Roles you would like to pursue" },
  { key: "location", label: "Location", hint: "Preferred countries, cities, or regions" },
  { key: "workPreferences", label: "Work Preferences", hint: "Workplace, employment, and availability preferences" },
  { key: "certifications", label: "Certifications", hint: "Certifications and issuers" },
  { key: "projects", label: "Projects", hint: "Projects, outcomes, and technologies" },
];

function displayValue(value: string) {
  return value.trim() || "Unknown";
}

export default function Home() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [draft, setDraft] = useState<Profile>(emptyProfile);
  const [editing, setEditing] = useState(false);
  const [fetchState, setFetchState] = useState<"idle" | "loading" | "complete" | "error">("idle");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  function openEditor() {
    setDraft(profile);
    setEditing(true);
  }

  function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfile(draft);
    setEditing(false);
  }

  async function fetchJobs() {
    setFetchState("loading");
    setErrorMessage("");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const candidateId = process.env.NEXT_PUBLIC_CANDIDATE_ID || defaultCandidateId;
      if (!candidateId) throw new Error("Candidate profile is not configured.");
      const response = await fetch(`${apiUrl}/fetch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_id: candidateId }),
      });
      if (!response.ok) throw new Error("Unable to fetch jobs right now.");
      const payload = (await response.json()) as { items?: SearchResult[] };
      setResults(payload.items || []);
      setFetchState("complete");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to fetch jobs right now.");
      setFetchState("error");
    }
  }

  async function downloadPdf() {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const candidateId = process.env.NEXT_PUBLIC_CANDIDATE_ID || defaultCandidateId;
      if (!candidateId) throw new Error("Candidate profile is not configured.");
      const response = await fetch(`${apiUrl}/search/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_id: candidateId }),
      });
      if (!response.ok) throw new Error("Unable to generate the PDF right now.");
      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "jobscatter-report.pdf";
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to generate the PDF right now.");
      setFetchState("error");
    }
  }

  return (
    <main className="profile-shell">
      <header className="site-header">
        <a className="brand" href="/">JobScatter <span>AI</span></a>
        <button className="profile-menu" type="button" aria-label="Open profile settings">Profile <span aria-hidden="true">⚙</span></button>
      </header>

      <section className="hero-copy">
        <p className="eyebrow">Finland job discovery</p>
        <h1>Find your next opportunity.</h1>
        <p className="intro">Fresh jobs from across Finland, in one place.</p>
      </section>

      <section className="profile-card" aria-labelledby="profile-summary-heading">
        <div className="card-kicker">Your profile</div>
        <div className="profile-card-body">
          <div>
            <h2 id="profile-summary-heading">{displayValue(profile.education)}</h2>
            <div className="profile-detail-block">
              <span>Target roles</span>
              <strong>{displayValue(profile.targetRoles)}</strong>
            </div>
            <div className="profile-detail-block">
              <span>Opportunity</span>
              <strong>{displayValue(profile.workPreferences)}</strong>
            </div>
            <div className="profile-detail-block">
              <span>Location</span>
              <strong>{displayValue(profile.location)}</strong>
            </div>
          </div>
          <button type="button" className="edit-profile-button" onClick={openEditor}>EDIT PROFILE</button>
        </div>
      </section>

      <section className="action-zone" aria-label="JobScatter actions">
        <button type="button" className="fetch-button" onClick={fetchJobs} disabled={fetchState === "loading"}>
          {fetchState === "loading" ? "FETCHING..." : "FETCH JOBS"}
        </button>
        <span>Find fresh jobs now</span>
        <button type="button" className="schedule-button">SCHEDULE</button>
        <span>Run automatically</span>
      </section>

      {fetchState === "loading" && <p className="fetch-status" role="status">Finding fresh jobs...</p>}
      {fetchState === "error" && <p className="fetch-status error-status" role="alert">{errorMessage}</p>}
      {fetchState === "complete" && (
        <ResultsScreen results={results} onDownload={downloadPdf} />
      )}

      {editing ? (
        <ProfileEditor draft={draft} onChange={setDraft} onSave={saveProfile} />
      ) : (
        <div className="profile-support" aria-label="Profile details">
          <span>Skills: {displayValue(profile.skills)}</span>
          <span>Capabilities: {displayValue(profile.capabilities)}</span>
          <span>Languages: {displayValue(profile.languages)}</span>
        </div>
      )}
    </main>
  );
}

function ResultsScreen({ results, onDownload }: { results: SearchResult[]; onDownload: () => void }) {
  return (
    <section className="results-screen" aria-labelledby="results-heading">
      <div className="results-header">
        <div>
          <p className="eyebrow">Latest search</p>
          <h2 id="results-heading">{results.length} {results.length === 1 ? "result" : "results"}</h2>
        </div>
        <button type="button" className="download-button" onClick={onDownload}>DOWNLOAD PDF</button>
      </div>
      {results.length === 0 ? (
        <p className="empty-results">No jobs matched this profile yet.</p>
      ) : (
        <div className="result-list">
          {results.map((result, index) => (
            <article className="result-row" key={`${result.job_link}-${index}`}>
              <div className="result-company">{result.company_name}</div>
              <div className="result-title">{result.job_title}</div>
              <time dateTime={result.posted_at}>{new Date(result.posted_at).toLocaleDateString()}</time>
              <a className="apply-link" href={result.job_link} target="_blank" rel="noreferrer">APPLY</a>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function ProfileSummary({ profile, onEdit }: { profile: Profile; onEdit: () => void }) {
  return (
    <section className="profile-summary" aria-labelledby="profile-summary-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Current profile</p>
          <h2 id="profile-summary-heading">Configured for you</h2>
        </div>
        <p className="profile-note">Your profile stays in your control.</p>
      </div>
      <div className="profile-grid">
        {profileFields.map(({ key, label }) => (
          <article className="profile-item" key={key}>
            <p>{label}</p>
            <strong>{displayValue(profile[key])}</strong>
          </article>
        ))}
      </div>
      <button type="button" className="edit-profile-button" onClick={onEdit}>EDIT PROFILE</button>
    </section>
  );
}

function ProfileEditor({ draft, onChange, onSave }: { draft: Profile; onChange: (profile: Profile) => void; onSave: (event: FormEvent<HTMLFormElement>) => void }) {
  return (
    <section className="profile-editor" aria-labelledby="profile-editor-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Profile editor</p>
          <h2 id="profile-editor-heading">Shape your profile</h2>
        </div>
        <p className="profile-note">Add what is true for you. Leave anything blank if it does not apply.</p>
      </div>
      <form onSubmit={onSave}>
        <div className="editor-grid">
          {profileFields.map(({ key, label, hint }) => (
            <label className="profile-field" key={key}>
              <span>{label}</span>
              <small>{hint}</small>
              <textarea
                aria-label={label}
                value={draft[key]}
                onChange={(event) => onChange({ ...draft, [key]: event.target.value })}
                rows={3}
              />
            </label>
          ))}
        </div>
        <div className="editor-actions">
          <button type="submit">SAVE PROFILE</button>
        </div>
      </form>
    </section>
  );
}
