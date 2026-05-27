import { Suspense } from "react";
import AnalysisPageContent from "./content";

// Static route — no dynamic segment.
// The match ID and team are passed as search params:
//   /analysis?match=sb%3A3749448&team=Arsenal
//
// Why static instead of /analysis/[id]?
// Next.js static export (output: 'export') pre-generates HTML files for every
// known route at build time. A dynamic route like /analysis/[id] requires
// generateStaticParams() to list every possible ID upfront — which we can't
// do because match IDs come from live APIs. Using a static route with search
// params means only one HTML file is needed (analysis/index.html), and any
// match can be loaded by the client-side JS without needing its own pre-built file.
export default function AnalysisPage() {
  return (
    <Suspense fallback={<div className="text-gray-400 text-sm">Loading…</div>}>
      <AnalysisPageContent />
    </Suspense>
  );
}
