import { Suspense } from "react";
import AnalysisPageContent from "./content";

export async function generateStaticParams() {
  // In Next.js 14.2.35, static export requires at least one pre-rendered page.
  // This placeholder allows building; client-side routing handles other IDs.
  return [
    { id: 'example' },
  ];
}

export const dynamicParams = true;

export default function AnalysisPage({
  params,
}: {
  params: { id: string };
}) {
  const id = decodeURIComponent(params.id);
  return (
    <Suspense
      fallback={<div className="text-gray-400 text-sm">Loading...</div>}
    >
      <AnalysisPageContent id={id} />
    </Suspense>
  );
}
