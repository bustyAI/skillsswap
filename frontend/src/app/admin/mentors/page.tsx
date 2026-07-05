"use client";

import { useState } from "react";
import { useAdminMentors, useToggleMentorEnabled } from "@/hooks/use-admin";
import type { AdminMentor } from "@/lib/types";

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function ToggleModal({
  mentor,
  onClose,
}: {
  mentor: AdminMentor;
  onClose: () => void;
}) {
  const [reason, setReason] = useState("");
  const toggleEnabled = useToggleMentorEnabled();
  const action = mentor.is_enabled ? "disable" : "enable";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;

    try {
      await toggleEnabled.mutateAsync({ userId: mentor.user_id, reason });
      onClose();
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-zinc-900">
          {mentor.is_enabled ? "Disable" : "Enable"} Mentor
        </h3>
        <p className="mt-1 text-sm text-zinc-600">
          {mentor.display_name ?? mentor.email}
        </p>

        <form onSubmit={handleSubmit} className="mt-4">
          <label className="block text-sm font-medium text-zinc-700">
            Reason
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
            placeholder={`Explain why this mentor is being ${action}d...`}
            required
          />

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
              disabled={toggleEnabled.isPending || !reason.trim()}
              className={`rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${
                mentor.is_enabled
                  ? "bg-red-600 hover:bg-red-700"
                  : "bg-green-600 hover:bg-green-700"
              }`}
            >
              {toggleEnabled.isPending
                ? "Processing..."
                : mentor.is_enabled
                  ? "Disable"
                  : "Enable"}
            </button>
          </div>

          {toggleEnabled.isError && (
            <p className="mt-2 text-sm text-red-600">
              Failed to {action} mentor. Please try again.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}

export default function AdminMentorsPage() {
  const [page, setPage] = useState(1);
  const [enabledOnly, setEnabledOnly] = useState(false);
  const [selectedMentor, setSelectedMentor] = useState<AdminMentor | null>(
    null
  );

  const { data, isLoading, error } = useAdminMentors(page, 20, enabledOnly);

  if (isLoading) {
    return <p className="text-zinc-500">Loading mentors...</p>;
  }

  if (error) {
    return <p className="text-red-600">Failed to load mentors.</p>;
  }

  const mentors = data?.mentors ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900">
          Mentor Management
        </h2>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={enabledOnly}
            onChange={(e) => {
              setEnabledOnly(e.target.checked);
              setPage(1);
            }}
            className="rounded border-zinc-300"
          />
          <span className="text-sm text-zinc-700">Enabled only</span>
        </label>
      </div>

      {mentors.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-600">No mentors found.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200">
            <thead className="bg-zinc-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Email
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Display Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Headline
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Rating
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Joined
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 bg-white">
              {mentors.map((mentor) => (
                <tr key={mentor.id}>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-900">
                    {mentor.email}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600">
                    {mentor.display_name ?? "-"}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-sm text-zinc-600">
                    {mentor.headline ?? "-"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600">
                    {mentor.rating_avg !== null
                      ? `${Number(mentor.rating_avg).toFixed(1)} (${mentor.rating_count})`
                      : "-"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600">
                    {formatDate(mentor.created_at)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {mentor.is_enabled ? (
                      <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                        Enabled
                      </span>
                    ) : (
                      <span className="inline-flex rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                        Disabled
                      </span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <button
                      onClick={() => setSelectedMentor(mentor)}
                      className={`text-sm font-medium ${
                        mentor.is_enabled
                          ? "text-red-600 hover:text-red-800"
                          : "text-green-600 hover:text-green-800"
                      }`}
                    >
                      {mentor.is_enabled ? "Disable" : "Enable"}
                    </button>
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

      {selectedMentor && (
        <ToggleModal
          mentor={selectedMentor}
          onClose={() => setSelectedMentor(null)}
        />
      )}
    </div>
  );
}
