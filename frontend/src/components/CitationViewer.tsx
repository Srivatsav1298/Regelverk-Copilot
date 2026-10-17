import type { Citation, Language } from "../types";

interface CitationViewerProps {
  citations: Citation[];
  language: Language;
}

export function CitationViewer({ citations, language }: CitationViewerProps) {
  const t = language === "nb" ? {
    header: "Verifiserte kilder fra lovverket",
    noSources: "Ingen eksplisitt lovhjemmel funnet i det indekserte korpuset.",
    openLovdata: "Åpne i Lovdata ↗",
    verified: "Verifisert sitat",
    unverified: "Ikke verifisert mot kilde",
  } : {
    header: "Verified Statutory Sources",
    noSources: "No explicit statutory source found in the reviewed corpus.",
    openLovdata: "Open in Lovdata ↗",
    verified: "Verified citation",
    unverified: "Unverified against source",
  };

  if (!citations || citations.length === 0) {
    return (
      <div className="citations-box empty">
        <p className="muted">{t.noSources}</p>
      </div>
    );
  }

  return (
    <div className="citations-box" role="region" aria-label={t.header}>
      <h4 className="citations-header">{t.header} ({citations.length})</h4>
      <div className="citation-cards">
        {citations.map((c, index) => (
          <details key={`${c.source_name}-${index}`} className="citation-detail" open={index === 0}>
            <summary className="citation-summary">
              <span className="source-title">📜 {c.source_name}</span>
              {c.verified !== undefined && (
                <span className={`verify-pill ${c.verified ? "verified" : "unverified"}`}>
                  {c.verified ? `✓ ${t.verified}` : `! ${t.unverified}`}
                </span>
              )}
            </summary>
            <div className="citation-body">
              <blockquote className="citation-excerpt">
                "{c.excerpt}"
              </blockquote>
              {c.url && (
                <a
                  href={c.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="lovdata-link"
                >
                  {t.openLovdata}
                </a>
              )}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
