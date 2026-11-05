import { useState } from "react";
import "./App.css";
import { Bar } from "react-chartjs-2";
import "chart.js/auto";
import { jsPDF } from "jspdf";
const API_URL = "https://hire-ai-recruitment-intelligence-9n.vercel.app";

function App() {
  const [uploadData, setUploadData] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState("");


  // Select PDF
  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    setUploadError("");
    setUploadData(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setSelectedFile(null);
      setUploadError("Please select a PDF file.");
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    setUploadError("");
    setUploadData(null);
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setSelectedFile(null);
      setUploadError("Please select a PDF file.");
      return;
    }
    setSelectedFile(file);
  };

  // Upload Resume PDF
  const uploadResume = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setUploadError("Please select a PDF resume first.");
      return;
    }

    setUploadLoading(true);
    setUploadError("");
    setUploadData(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${API_URL}/upload-resume`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "Resume upload failed."
        );
      }

      setUploadData(result);
    } catch (err) {
      setUploadError(err.message || "Unable to connect to the backend.");
    } finally {
      setUploadLoading(false);
    }
  };

  // Convert score to percentage.
  // Backend scores are currently on a 0–100 scale.
  const toPercent = (value) => `${Number(value ?? 0).toFixed(1)}%`;

  // Display Job Recommendations
  const renderJobCards = (recommendations = []) => {
    if (!recommendations.length) {
      return <p>No job recommendations found.</p>;
    }

    return recommendations.map((job, index) => (
      <div className="job-card" key={job.job_id ?? index}>
        <h3>{job.title}</h3>
        <p>Job ID: {job.job_id}</p>

        <p>
          <strong>Match Score:</strong> {toPercent(job.combined_score ?? job.similarity_score)}
        </p>
        <p>
          <strong>Similarity:</strong> {toPercent(job.similarity_score)}
        </p>
        <p>
          <strong>Skill Coverage:</strong> {toPercent(job.skill_coverage)}
        </p>

        {job.match_explanation && (
          <p className="match-explanation">{job.match_explanation}</p>
        )}

        {job.required_skill_count !== undefined && (
          <p>
            <strong>Skills Matched:</strong>{" "}
            {job.matched_skill_count}/{job.required_skill_count}
          </p>
        )}

        <div className="skill-columns">
          <div>
            <strong>Matched Skills</strong>
            <div className="skills">
              {(job.matched_skills || []).length ? (
                job.matched_skills.map((skill) => (
                  <span className="skill matched" key={skill}>
                    {skill}
                  </span>
                ))
              ) : (
                <span>None</span>
              )}
            </div>
          </div>

          <div>
            <strong>Missing Skills</strong>
            <div className="skills">
              {(job.missing_skills || []).length ? (
                job.missing_skills.map((skill) => (
                  <span className="skill missing" key={skill}>
                    {skill}
                  </span>
                ))
              ) : (
                <span>None</span>
              )}
            </div>
          </div>
        </div>
      </div>
    ));
  };

  const currentResults = uploadData;
  const recommendations = currentResults?.recommendations || [];
  // Dashboard Summary Calculations
const bestMatch = recommendations.length
  ? Math.max(
      ...recommendations.map((job) =>
        Number(job.combined_score ?? job.similarity_score ?? 0)
      )
    )
  : 0;

const averageMatch = recommendations.length
  ? recommendations.reduce(
      (sum, job) =>
        sum + Number(job.combined_score ?? job.similarity_score ?? 0),
      0
    ) / recommendations.length
  : 0;

const totalJobs = recommendations.length;

  // Create a professional PDF report from the currently displayed results.
  const downloadReport = () => {
    if (!currentResults) {
      alert("Please search for a candidate or upload a resume first.");
      return;
    }

    try {
      const doc = new jsPDF({ unit: "mm", format: "a4" });
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 16;
      const contentWidth = pageWidth - margin * 2;
      const bottomLimit = pageHeight - 21;
      let y = 20;

      const addFooter = () => {
        const totalPages = doc.internal.getNumberOfPages();
        for (let page = 1; page <= totalPages; page += 1) {
          doc.setPage(page);
          doc.setDrawColor(220, 224, 238);
          doc.line(margin, pageHeight - 14, pageWidth - margin, pageHeight - 14);
          doc.setFont("helvetica", "normal");
          doc.setFontSize(8);
          doc.setTextColor(115, 123, 145);
          doc.text("HireAI | AI Recruitment Intelligence", margin, pageHeight - 8);
          doc.text(`Page ${page} of ${totalPages}`, pageWidth - margin, pageHeight - 8, { align: "right" });
        }
      };

      const newPage = () => {
        doc.addPage();
        y = 20;
      };

      const ensureSpace = (height) => {
        if (y + height > bottomLimit) newPage();
      };

      const wrappedLines = (text, width, size = 10, bold = false) => {
        doc.setFont("helvetica", bold ? "bold" : "normal");
        doc.setFontSize(size);
        return doc.splitTextToSize(String(text ?? "Not available"), width);
      };

      const addText = (text, options = {}) => {
        const { size = 10, bold = false, gap = 5, color = [45, 55, 83] } = options;
        const lines = wrappedLines(text, contentWidth, size, bold);
        const lineHeight = size * 0.42 + 0.5;
        ensureSpace(lines.length * lineHeight + gap);
        doc.setFont("helvetica", bold ? "bold" : "normal");
        doc.setFontSize(size);
        doc.setTextColor(...color);
        doc.text(lines, margin, y);
        y += lines.length * lineHeight + gap;
      };

      const addSection = (title) => {
        ensureSpace(17);
        y += 2;
        doc.setFillColor(240, 238, 255);
        doc.roundedRect(margin, y - 5, contentWidth, 11, 2, 2, "F");
        doc.setFont("helvetica", "bold");
        doc.setFontSize(11.5);
        doc.setTextColor(56, 48, 133);
        doc.text(title, margin + 4, y + 2.5);
        y += 13;
      };

      const score = (job) => Number(job.combined_score ?? job.similarity_score ?? 0);
      const best = recommendations.length ? Math.max(...recommendations.map(score)) : 0;
      const average = recommendations.length
        ? recommendations.reduce((sum, job) => sum + score(job), 0) / recommendations.length
        : 0;

      // Cover/header
      doc.setFillColor(32, 38, 83);
      doc.rect(0, 0, pageWidth, 43, "F");
      doc.setFillColor(103, 84, 207);
      doc.rect(0, 40, pageWidth, 3, "F");
      doc.setTextColor(255, 255, 255);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(24);
      doc.text("HireAI", margin, 18);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10.5);
      doc.text("RESUME & JOB MATCH ANALYSIS", margin, 27);
      doc.setFontSize(9);
      doc.setTextColor(220, 224, 255);
      doc.text(`Generated: ${new Date().toLocaleDateString()}`, margin, 35);
      y = 53;

      addSection("1. Candidate Profile");
      if (uploadData) {
        addText(`Resume File: ${uploadData.filename || selectedFile?.name || "Not available"}`);
        addText(`Extracted Skills: ${(uploadData.extracted_skills || []).join(", ") || "No skills detected"}`);
        // Keep private contact details out of the report preview.
      }

      addSection("2. Match Score Summary");
      const cardGap = 4;
      const metricWidth = (contentWidth - cardGap * 2) / 3;
      const metricHeight = 23;
      ensureSpace(metricHeight + 5);
      const metricY = y;
      [
        { label: "BEST MATCH", value: `${best.toFixed(1)}%` },
        { label: "AVERAGE MATCH", value: `${average.toFixed(1)}%` },
        { label: "RECOMMENDED JOBS", value: String(recommendations.length) },
      ].forEach((metric, i) => {
        const x = margin + i * (metricWidth + cardGap);
        doc.setFillColor(248, 247, 255);
        doc.setDrawColor(225, 222, 248);
        doc.roundedRect(x, metricY, metricWidth, metricHeight, 2, 2, "FD");
        doc.setFont("helvetica", "normal");
        doc.setFontSize(7);
        doc.setTextColor(100, 105, 130);
        doc.text(metric.label, x + 3, metricY + 7);
        doc.setFont("helvetica", "bold");
        doc.setFontSize(14);
        doc.setTextColor(92, 74, 190);
        doc.text(metric.value, x + 3, metricY + 17);
      });
      y += metricHeight + 8;

      addSection("3. Recommended Jobs");
      if (!recommendations.length) addText("No job recommendations were available.");

      recommendations.forEach((job, index) => {
        const pad = 4;
        const innerWidth = contentWidth - pad * 2;
        const detailItems = [
          { label: "Job ID: ", value: String(job.job_id ?? "Not available"), color: [48, 57, 83] },
          {
            label: "Match Score: ",
            value: `${score(job).toFixed(1)}% | Similarity: ${Number(job.similarity_score ?? 0).toFixed(1)}% | Skill Coverage: ${Number(job.skill_coverage ?? 0).toFixed(1)}%`,
            color: [48, 57, 83],
          },
          { label: "Matched Skills: ", value: (job.matched_skills || []).join(", ") || "None listed", color: [25, 125, 76] },
          { label: "Missing Skills: ", value: (job.missing_skills || []).join(", ") || "None listed", color: [175, 104, 25] },
        ];
        if (job.match_explanation) detailItems.push({ label: "Explanation: ", value: job.match_explanation, color: [48, 57, 83] });

        const title = `${index + 1}. ${job.title || "Untitled Job"}`;
        const titleLines = wrappedLines(title, innerWidth, 10.5, true);
        const measuredDetails = detailItems.map((item) => ({
          ...item,
          lines: wrappedLines(`${item.label}${item.value}`, innerWidth, 8.8, false),
        }));
        const titleHeight = titleLines.length * 4.8 + 3;
        const detailHeight = measuredDetails.reduce((sum, item) => sum + item.lines.length * 4.1 + 2.5, 0);
        const cardHeight = pad * 2 + titleHeight + detailHeight;

        // Keep a whole card on one page whenever it can fit on a page.
        if (y + cardHeight > bottomLimit) {
          newPage();
        }

        const cardY = y;
        doc.setFillColor(250, 250, 255);
        doc.setDrawColor(225, 228, 241);
        doc.roundedRect(margin, cardY, contentWidth, cardHeight, 2, 2, "FD");

        let textY = cardY + pad + 3;
        doc.setFont("helvetica", "bold");
        doc.setFontSize(10.5);
        doc.setTextColor(39, 47, 91);
        doc.text(titleLines, margin + pad, textY);
        textY += titleHeight;

        measuredDetails.forEach((item) => {
          doc.setFont("helvetica", "normal");
          doc.setFontSize(8.8);
          doc.setTextColor(...item.color);
          doc.text(item.lines, margin + pad, textY);
          textY += item.lines.length * 4.1 + 2.5;
        });

        y = cardY + cardHeight + 4;
      });

      addSection("4. Skill Development Recommendations");
      const missingCounts = {};
      recommendations.forEach((job) => {
        (job.missing_skills || []).forEach((skill) => {
          const name = String(skill).trim();
          if (name) missingCounts[name] = (missingCounts[name] || 0) + 1;
        });
      });
      const priorities = Object.entries(missingCounts).sort((a, b) => b[1] - a[1]);
      if (!priorities.length) {
        addText("No missing skills were identified in the available recommendations.");
      } else {
        addText("Prioritize skills that appear most frequently among recommended jobs:");
        priorities.slice(0, 15).forEach(([skill, count], index) => {
          addText(`${index + 1}. ${skill} — missing in ${count} recommended job(s)`, { size: 9, gap: 3 });
        });
        addText("Suggested action: practice these skills through projects and update your resume as you gain experience.", {
          size: 9,
          color: [56, 48, 133],
        });
      }

      addSection("5. Report Notes");
      addText("This report summarizes results returned by the HireAI recommendation system. Match scores are estimates based on the available data and should be used as guidance, not as a guarantee of job suitability.", { size: 9 });

      addFooter();
      const baseName = uploadData?.filename
        ? uploadData.filename.replace(/\.pdf$/i, "")
        : "Resume";
      const safeName = String(baseName).replace(/[^a-z0-9-_]/gi, "_").replace(/_+/g, "_");
      doc.save(`HireAI_Report_${safeName}.pdf`);
    } catch (err) {
      console.error("PDF generation failed:", err);
      alert("Unable to generate the PDF report. Please try again.");
    }
  };

const jobMatchChartData = {
  labels: recommendations.map((job) => job.title),
  datasets: [
    {
      label: "Job Match Score (%)",
      data: recommendations.map((job) => {
        const score = Number(
          job.combined_score ?? job.similarity_score ?? 0
        );

        return Math.max(0, Math.min(100, score));
      }),
      backgroundColor: "#0f005c",
      borderRadius: 6,
    },
  ],
};

const jobMatchChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: "y",
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: (context) => `Match Score: ${context.raw.toFixed(1)}%`,
      },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      max: 100,
      title: {
        display: true,
        text: "Match Score (%)",
      },
    },
  },
};
  // Skill Gap Analysis: rank missing skills by frequency.
  const skillCounts = {};

  recommendations.forEach((job) => {
    (job.missing_skills || []).forEach((skill) => {
      const normalized = skill.trim().toLowerCase();
      skillCounts[normalized] = (skillCounts[normalized] || 0) + 1;
    });
  });

  const prioritySkills = Object.entries(skillCounts).sort(
    (a, b) => b[1] - a[1] || a[0].localeCompare(b[0])
  );

  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="HireAI home">
          <span className="brand-mark">H<span>+</span></span>
          <span><strong>HIRE<span>AI</span></strong><small>RECRUITMENT INTELLIGENCE</small></span>
        </a>
        <div className="system-status"><span className="status-dot" /> AI ENGINE <b>READY</b></div>
      </header>

      <main className="main-content" id="top">
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span /> INTELLIGENT CAREER MATCHING / 01</div>
            <h1>Your next move,<br /><span>decoded.</span></h1>
            <p>Upload your resume. Let HireAI map your skills to relevant opportunities and reveal what to learn next.</p>
            <div className="hero-tags"><span>01 / RESUME PARSING</span><span>02 / SKILL MATCHING</span><span>03 / JOB DISCOVERY</span></div>
          </div>
          <div className="hero-graphic" aria-hidden="true">
            <div className="orbit orbit-one" /><div className="orbit orbit-two" />
            <div className="core"><span>H</span><small>AI</small></div>
            <span className="node node-one">SKILLS</span><span className="node node-two">MATCH</span><span className="node node-three">DATA</span>
            <div className="graphic-caption">MATCH ENGINE <b>● ONLINE</b></div>
          </div>
        </section>

        <section className="upload-section" aria-labelledby="upload-title">
          <div className="section-kicker">// START ANALYSIS <span>STEP 01</span></div>
          <div className="upload-heading">
            <div><h2 id="upload-title">Feed the <span>intelligence.</span></h2><p>Upload a text-based PDF resume to generate your personalized job match report.</p></div>
            <div className="file-spec">SUPPORTED FORMAT <strong>PDF / MAX 1 FILE</strong></div>
          </div>

          <form className="upload-box" onSubmit={uploadResume} onDragOver={(event) => event.preventDefault()} onDrop={handleDrop}>
            <div className="upload-symbol"><span>↑</span></div>
            <h3>{selectedFile ? "Resume ready for analysis" : "Drop your resume into the system"}</h3>
            <p>{selectedFile ? "File selected. Run the analysis when you're ready." : "Drag and drop your PDF here, or browse files"}</p>
            <label className="browse-button" htmlFor="resume-file">{selectedFile ? "CHANGE FILE" : "BROWSE RESUME"}</label>
            <input id="resume-file" className="upload-input" type="file" accept=".pdf,application/pdf" onChange={handleFileChange} />
            {selectedFile && <div className="selected-file"><span className="pdf-badge">PDF</span><span>{selectedFile.name}</span><button type="button" className="remove-file" onClick={() => { setSelectedFile(null); setUploadData(null); setUploadError(""); }}>REMOVE</button></div>}
            <div className="upload-footnote"><span>⌁ SECURE LOCAL PROCESSING</span><span>TEXT-BASED PDF RECOMMENDED</span></div>
            <button className="upload-button" type="submit" disabled={uploadLoading || !selectedFile}>
              {uploadLoading ? <><span className="spinner" /> ANALYZING RESUME...</> : <>ANALYZE RESUME <span>↗</span></>}
            </button>
          </form>
          {uploadError && <p className="error-message">{uploadError}</p>}
          {uploadLoading && <div className="processing-note"><span className="status-dot" /> Parsing resume · identifying skills · calculating job matches</div>}
        </section>

        {uploadData && (
          <section className="results-section">
            <div className="section-kicker">// ANALYSIS COMPLETE <span>RESULTS READY</span></div>
            <div className="results-title-row"><div><h2>Your match <span>intelligence.</span></h2><p className="section-subtitle">Review the roles that align with your resume and the skills that could strengthen your profile.</p></div><button className="download-report-button" type="button" onClick={downloadReport}>↓ DOWNLOAD REPORT</button></div>
            <div className="summary-cards">
              <div className="summary-card"><span className="metric-label">01 / TOP MATCH</span><p className="summary-value">{bestMatch.toFixed(1)}<small>%</small></p><span>Highest job similarity score</span></div>
              <div className="summary-card"><span className="metric-label">02 / AVG. MATCH</span><p className="summary-value">{averageMatch.toFixed(1)}<small>%</small></p><span>Across recommended roles</span></div>
              <div className="summary-card"><span className="metric-label">03 / OPPORTUNITIES</span><p className="summary-value">{totalJobs.toString().padStart(2, "0")}</p><span>Jobs matched to your resume</span></div>
            </div>
            <div className="profile-strip"><div><span className="metric-label">RESUME ANALYZED</span><strong>{uploadData.filename || selectedFile?.name || "Uploaded PDF"}</strong></div><div><span className="metric-label">SKILLS IDENTIFIED</span><strong>{(uploadData.extracted_skills || []).length} skills detected</strong></div></div>
            <div className="chart-panel"><div className="panel-heading"><div><span className="metric-label">MATCH ANALYTICS / 01</span><h3>Opportunity match scores</h3><p>Compare estimated relevance across recommended roles.</p></div><span className="panel-index">FIG. 01</span></div>
              {recommendations.length > 0 ? <div className="chart-container"><Bar data={jobMatchChartData} options={jobMatchChartOptions} /></div> : <p>No recommendations available for the chart.</p>}
            </div>
            <div className="skill-gap-panel"><div className="panel-heading"><div><span className="metric-label">SKILL INTELLIGENCE / 02</span><h3>Your skill gap radar</h3><p>Skills appearing in the requirements that were not detected in your resume.</p></div><span className="panel-index">FIG. 02</span></div>
              {prioritySkills.length > 0 ? <div className="skill-gap-list">{prioritySkills.map(([skill, count]) => <div className="skill-gap-item" key={skill}><div><strong>{skill}</strong><p>Missing in {count} of {recommendations.length} recommended jobs</p></div><span className="priority-badge">{count >= 3 ? "HIGH PRIORITY" : count === 2 ? "MEDIUM PRIORITY" : "LEARN"}</span></div>)}</div> : <p className="empty-state">No missing skills were identified for these recommendations.</p>}
            </div>
            <div className="jobs-heading"><div><span className="metric-label">RECOMMENDATIONS / 03</span><h3>Roles worth exploring</h3></div><span>{recommendations.length.toString().padStart(2, "0")} RESULTS</span></div>
            {renderJobCards(recommendations)}
            <div className="results-disclaimer">HireAI match scores are estimates based on available resume and job data. Use them as guidance, not as a guarantee of job suitability.</div>
          </section>
        )}
        <footer className="footer"><span>HIREAI <b>///</b> RECRUITMENT INTELLIGENCE</span><span>BUILT FOR YOUR NEXT MOVE <b>↗</b></span></footer>
      </main>
    </div>
  );
}

export default App;