"use client";

import { useState } from "react";
import { useAdminUserSearch, useBanUser } from "@/hooks/use-admin";
import type { AdminUser } from "@/lib/types";

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function BanModal({
  user,
  onClose,
}: {
  user: AdminUser;
  onClose: () => void;
}) {
  const [reason, setReason] = useState("");
  const banUser = useBanUser();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;

    try {
      await banUser.mutateAsync({ userId: user.id, reason });
      onClose();
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-zinc-900">Ban User</h3>
        <p className="mt-1 text-sm text-zinc-600">
          Banning {user.display_name ?? user.email}
        </p>

        <form onSubmit={handleSubmit} className="mt-4">
          <label className="block text-sm font-medium text-zinc-700">
            Reason for ban
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
            placeholder="Explain why this user is being banned..."
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
              disabled={banUser.isPending || !reason.trim()}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {banUser.isPending ? "Banning..." : "Ban User"}
            </button>
          </div>

          {banUser.isError && (
            <p className="mt-2 text-sm text-red-600">
              Failed to ban user. Please try again.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}

export default function AdminUsersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [page, setPage] = useState(1);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);

  const { data, isLoading, error } = useAdminUserSearch(searchQuery, page);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(searchInput);
    setPage(1);
  };

  const users = data?.users ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <div>
      <h2 className="text-lg font-semibold text-zinc-900">User Search</h2>

      <form onSubmit={handleSearch} className="mt-4 flex gap-2">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by email..."
          className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
        />
        <button
          type="submit"
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
        >
          Search
        </button>
      </form>

      {searchQuery && (
        <div className="mt-4">
          {isLoading ? (
            <p className="text-zinc-500">Searching...</p>
          ) : error ? (
            <p className="text-red-600">Failed to search users.</p>
          ) : users.length === 0 ? (
            <p className="text-sm text-zinc-600">
              No users found matching &quot;{searchQuery}&quot;
            </p>
          ) : (
            <>
              <div className="overflow-x-auto">
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
                        Joined
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                        Mentor
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-zinc-500">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200 bg-white">
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-900">
                          {user.email}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600">
                          {user.display_name ?? "-"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600">
                          {formatDate(user.created_at)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          {user.banned_at ? (
                            <span className="inline-flex rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                              Banned
                            </span>
                          ) : (
                            <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                              Active
                            </span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600">
                          {user.has_mentor_profile ? "Yes" : "No"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          {user.banned_at ? (
                            <span className="text-sm text-zinc-400">-</span>
                          ) : (
                            <button
                              onClick={() => setSelectedUser(user)}
                              className="text-sm font-medium text-red-600 hover:text-red-800"
                            >
                              Ban
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

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
            </>
          )}
        </div>
      )}

      {selectedUser && (
        <BanModal user={selectedUser} onClose={() => setSelectedUser(null)} />
      )}
    </div>
  );
}
