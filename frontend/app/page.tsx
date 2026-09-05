"use client";

import React from "react";
import { FormEvent, useEffect, useState } from "react";

type JobSource = {
  source: string;
  application_url: string;
};

type Job = {
  job_id: string;
  company: string | null;
  title: string | null;
  locations: string[] | null;
  workplace_type: string | null;
  opportunity_type: string | null;
  posted_at: string | null;
  application_url: string | null;
  source_records: JobSource[];
};

type JobsResponse = {
  items: Job[];
  page: number;
  page_size: number;
  total: number;
};

type Filters = {
  search: string;
  it_field: string;
  opportunity_type: string;
  experience_suitability: string;
  location: string;
  workplace_type: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const PAGE_SIZE = 12;
const IT_FIELDS = [
  "AI / Machine Learning",
  "Software Engineering",
  "Data",
  "Cloud / DevOps",
  "Cybersecurity",
  "IT / Systems",
  "QA / Testing",
  "Networking",
  "Embedded / IoT",
  "Robotics / Automation",
  "Web / Digital Technology",
  "Enterprise / Business IT",
  "Research / R&D",
  "Technical Product / Solutions",
  "Other IT / Technology",
  "Unknown",
];
const OPPORTUNITY_TYPES = ["employment", "internship", "contract", "part-time", "full-time"];
const EXPERIENCE_OPTIONS = ["highest", "high", "suitable/lower", "ineligible", "unknown"];
const WORKPLACE_TYPES = ["remote", "hybrid", "on-site", "Unknown"];

const initialFilters: Filters = {
  search: "",
  it_field: "",
  opportunity_type: "",
  experience_suitability: "",
  location: "",
  workplace_type: "",
};

function displayValue(value: string | null | undefined) {
  return value?.trim() || "Unknown";
}

function formatPostedTime(value: string | null) {
  if (!value) return "Unknown";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Unknown"
    : new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(date);
}

function buildQuery(filters: Filters, page: number) {
  const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

export default function Home() {
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [submittedFilters, setSubmittedFilters] = useState<Filters>(initialFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<JobsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    fetch(`${API_URL}/jobs?${buildQuery(submittedFilters, page)}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("The jobs could not be loaded.");
        return response.json() as Promise<JobsResponse>;
      })
      .then(setData)
      .catch((requestError: Error) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [page, submittedFilters]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setSubmittedFilters(filters);
  }

  function clearFilters() {
    setFilters(initialFilters);
    setPage(1);
    setSubmittedFilters(initialFilters);
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <main className="job-finder-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">JobScout AI</p>
          <h1>Find work that fits.</h1>
          <p className="intro">A clear view of current technology roles, gathered in one place.</p>
        </div>
        <div className="status-mark" aria-label="Job search is live"><span /> Live search</div>
      </header>

      <section className="search-panel" aria-label="Job search filters">
        <form onSubmit={handleSubmit}>
          <label className="search-field">
            <span>Search jobs</span>
            <input
              value={filters.search}
              onChange={(event) => setFilters({ ...filters, search: event.target.value })}
              placeholder="Title, company, or keyword"
            />
          </label>
          <div className="filter-grid">
            <FilterSelect label="IT field" value={filters.it_field} options={IT_FIELDS} onChange={(value) => setFilters({ ...filters, it_field: value })} />
            <FilterSelect label="Opportunity" value={filters.opportunity_type} options={OPPORTUNITY_TYPES} onChange={(value) => setFilters({ ...filters, opportunity_type: value })} />
            <FilterSelect label="Experience" value={filters.experience_suitability} options={EXPERIENCE_OPTIONS} onChange={(value) => setFilters({ ...filters, experience_suitability: value })} />
            <label>
              <span>Location</span>
              <input value={filters.location} onChange={(event) => setFilters({ ...filters, location: event.target.value })} placeholder="City or country" />
            </label>
            <FilterSelect label="Workplace" value={filters.workplace_type} options={WORKPLACE_TYPES} onChange={(value) => setFilters({ ...filters, workplace_type: value })} />
          </div>
          <div className="filter-actions">
            <button type="submit">Search jobs</button>
            <button type="button" className="quiet-button" onClick={clearFilters}>Clear filters</button>
          </div>
        </form>
      </section>

      <section className="results-section" aria-live="polite">
        <div className="results-heading">
          <div>
            <p className="eyebrow">Open roles</p>
            <h2>{loading && !data ? "Searching roles" : `${data?.total ?? 0} matching jobs`}</h2>
          </div>
          {data && data.total > 0 && <p className="result-count">Page {data.page} of {totalPages}</p>}
        </div>

        {loading && <div className="message-panel">Loading jobs...</div>}
        {!loading && error && <div className="message-panel error-panel"><strong>We could not load the jobs.</strong><span>{error}</span><button type="button" onClick={() => setSubmittedFilters({ ...submittedFilters })}>Try again</button></div>}
        {!loading && !error && data?.items.length === 0 && <div className="message-panel"><strong>No matching jobs.</strong><span>Try broadening your search or clearing a filter.</span></div>}
        {!loading && !error && data && data.items.length > 0 && (
          <div className="job-list">
            {data.items.map((job) => <JobCard key={job.job_id} job={job} />)}
          </div>
        )}

        {!loading && !error && data && data.total > 0 && (
          <nav className="pagination" aria-label="Job results pages">
            <button type="button" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
            <span>Page {page} of {totalPages}</span>
            <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
          </nav>
        )}
      </section>
    </main>
  );
}

function FilterSelect({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Any</option>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </label>
  );
}

function JobCard({ job }: { job: Job }) {
  const source = job.source_records[0];
  const applicationUrl = job.application_url || source?.application_url;
  return (
    <article className="job-card">
      <div className="job-card-main">
        <p className="job-company">{displayValue(job.company)}</p>
        <h3>{displayValue(job.title)}</h3>
        <div className="job-meta">
          <span>{job.locations?.length ? job.locations.join(", ") : "Unknown"}</span>
          <span>{displayValue(job.workplace_type)}</span>
          <span>{displayValue(job.opportunity_type)}</span>
          <span>Posted {formatPostedTime(job.posted_at)}</span>
        </div>
      </div>
      <div className="job-card-action">
        <span className="source-label">Source: {displayValue(source?.source)}</span>
        {applicationUrl ? <a href={applicationUrl} target="_blank" rel="noreferrer">Apply directly <span aria-hidden="true">-&gt;</span></a> : <span className="unavailable-link">Application link unavailable</span>}
      </div>
    </article>
  );
}
