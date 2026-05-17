import { api } from "@/lib/api";
import type { AnalysisRecord } from "@/lib/api";
import HistoryList from "@/components/HistoryList";
import Link from "next/link";

export default async function HistoryPage() {
  let analyses: AnalysisRecord[] = [];
  try {
    analyses = await api.getAnalyses();
  } catch {
    // backend unreachable
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">History</h2>
          <p className="text-gray-400 text-sm mt-1">All saved analyses, newest first.</p>
        </div>
        <Link href="/" className="text-sm text-gray-400 hover:text-gray-200 transition-colors">
          ← New analysis
        </Link>
      </div>

      <HistoryList analyses={analyses} />
    </div>
  );
}
