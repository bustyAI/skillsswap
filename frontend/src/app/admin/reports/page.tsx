"use client";

import { useState } from "react";
import { useAdminReports, useResolveReport } from "@/hooks/use-admin";
import type { ReportStatus, AdminReport } from "@/lib/types";

const statusOptions: { value: ReportStatus | "ALL"; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "PENDING", label: "Pending" },
  { value: "UNDER_REVIEW", label: "Under Review" },
  { value: "RESOLVED", label: "Resolved" },
  { value: "DISMISSED", label: "Dismissed" },
];

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusBadge({ status }: { status: ReportStatus }) {
  const styles: Record<ReportStatus, string> = {
    PENDING: "bg-yellow-100 text-yellow-800",
    UNDER_REVIEW: "bg-blue-100 text-blue-800",
    RESOLVED: "bg-green-100 text-green-800",
    DISMISSED: "bg-zinc-100 text-zinc-800",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${styles[status]}`}
    >
      {status}
    </span>
  );
}

function ResolveModal({
  report,
  onClose,
}: {
  report: AdminReport;
  onClose: () => void;
}) {
  const [notes, setNotes] = useState("");
  const [dismiss, setDismiss] = useState(false);
  const resolveReport = useResolveReport();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) return;

    try {
      await resolveReport.mutateAsync({
        reportId: report.id,
        data: { resolution_notes: notes, dismiss },
      });
      onClose();
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-zinc-900">Resolve Report</h3>
        <p className="mt-1 text-sm text-zinc-600">
          Report by {report.reporter?.email ?? "Unknown"}
        </p>

        <div className="mt-4 rounded-md bg-zinc-50 p-3">
          <p className="text-sm font-medium text-zinc-700">Reason:</p>
          <p className="mt-1 text-sm text-zinc-600">{report.reason}</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-4">
          <label className="block text-sm font-medium text-zinc-700">
            Resolution Notes
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
            placeholder="Describe the action taken..."
            required
          />

          <label className="mt-4 flex items-center gap-2">
            <input
              type="checkbox"
              checked={dismiss}
              onChange={(e) => setDismiss(e.target.checked)}
              className="rounded border-zinc-300"
            />
            <span className="text-sm text-zinc-700">
              Dismiss (no action needed)
            </span>
          </label>

          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={resolveReport.isPending || !notes.trim()}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
            >
              {resolveReport.isPending ? "Submitting..." : "Submit"}
            </button>
          </div>

          {resolveReport.isError && (
            <p className="mt-2 text-sm text-red-600">
              Failed to resolve report. Please try again.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}

export default function AdminReportsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<ReportStatus | undefined>();
  const [selectedReport, setSelectedReport] = useState<AdminReport | null>(
    null
  );

  const { data, isLoading, error } = useAdminReports(page, 20, statusFilter);

  if (isLoading) {
    return <p className="text-zinc-500">Loading reports...</p>;
  }

  if (error) {
    return <p className="text-red-600">Failed to load reports.</p>;
  }

  const reports = data?.reports ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900">Report Queue</h2>
        <select
          value={statusFilter ?? "ALL"}
          onChange={(e) =>
            setStatusFilter(
              e.target.value === "ALL"
                ? undefined
                : (e.target.value as ReportStatus)
            )
          }
          className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {reports.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-600">No reports found.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200">
            <thead className="bg-zinc-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Reporter
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Reported User
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Reason
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Created
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 bg-white">
              {reports.map((report) => (
                <tr key={report.id}>
                  <td className="whitespace-nowrap px-4 py-3">
                    <StatusBadge status={report.status} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-900">
                    {report.reporter?.email ?? "Unknown"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-900">
                    {report.reported_user?.email ?? "N/A"}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-sm text-zinc-600">
                    {report.reason}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600">
                    {formatDate(report.created_at)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {report.status === "PENDING" ||
                    report.status === "UNDER_REVIEW" ? (
                      <button
                        onClick={() => setSelectedReport(report)}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        Resolve
                      </button>
                    ) : (
                      <span className="text-sm text-zinc-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-zinc-600">
            Page {page} of {totalPages} ({total} total)
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-md border border-zinc-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="rounded-md border border-zinc-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {selectedReport && (
        <ResolveModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </div>
  );
}
