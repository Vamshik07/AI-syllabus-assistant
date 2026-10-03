"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Subject } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { GraduationCap, Plus, ArrowRight, BookOpen, Pencil, Trash2, Lock, LogIn, UserPlus } from "lucide-react";

export default function SubjectsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  // Edit state
  const [editingSubject, setEditingSubject] = useState<Subject | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [updating, setUpdating] = useState(false);

  // Delete state
  const [deletingSubject, setDeletingSubject] = useState<Subject | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadSubjects = async () => {
    try {
      setLoading(true);
      const data = await api.getSubjects();
      setSubjects(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (isAuthenticated) {
        loadSubjects();
      } else {
        setLoading(false);
      }
    }
  }, [isAuthenticated, authLoading]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      setCreating(true);
      await api.createSubject({ name: name.trim(), description: description.trim() || undefined });
      setName("");
      setDescription("");
      setShowCreateModal(false);
      loadSubjects();
    } finally {
      setCreating(false);
    }
  };

  const openEditModal = (e: React.MouseEvent, s: Subject) => {
    e.preventDefault();
    e.stopPropagation();
    setEditingSubject(s);
    setEditName(s.name);
    setEditDesc(s.description || "");
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSubject || !editName.trim()) return;
    try {
      setUpdating(true);
      await api.updateSubject(editingSubject.id, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
      });
      setEditingSubject(null);
      loadSubjects();
    } catch (err: any) {
      alert(err.message || "Failed to update subject.");
    } finally {
      setUpdating(false);
    }
  };

  const openDeleteModal = (e: React.MouseEvent, s: Subject) => {
    e.preventDefault();
    e.stopPropagation();
    setDeletingSubject(s);
  };

  const handleDelete = async () => {
    if (!deletingSubject) return;
    try {
      setDeleting(true);
      await api.deleteSubject(deletingSubject.id);
      setDeletingSubject(null);
      loadSubjects();
    } catch (err: any) {
      alert(err.message || "Failed to delete subject.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">All Subjects</h1>
          <p className="text-xs text-gray-500">
            Create or manage your study subjects and units.
          </p>
        </div>
      {isAuthenticated && (
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          <span>New Subject</span>
        </button>
      )}
      </div>

      {!authLoading && !isAuthenticated ? (
        <div className="rounded-3xl border border-indigo-100 bg-white p-10 text-center shadow-lg shadow-indigo-50/50 max-w-lg mx-auto my-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 mx-auto mb-4">
            <Lock className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Sign In to Access Your Subjects</h2>
          <p className="mt-2 text-xs text-gray-500 leading-relaxed">
            Your study subjects, uploaded syllabus resources, and quiz mastery progress are securely stored in your personal account.
          </p>
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/login"
              className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-indigo-700 transition-all"
            >
              <LogIn className="h-4 w-4" />
              <span>Sign In</span>
            </Link>
            <Link
              href="/register"
              className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl border border-gray-300 bg-white px-5 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <UserPlus className="h-4 w-4" />
              <span>Create Account</span>
            </Link>
          </div>
        </div>
      ) : loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 rounded-2xl bg-gray-100 animate-pulse border border-gray-200" />
          ))}
        </div>
      ) : subjects.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-gray-300 bg-white p-12 text-center">
          <GraduationCap className="h-10 w-10 text-gray-400 mx-auto mb-2" />
          <p className="font-semibold text-gray-800 text-sm">No subjects yet</p>
          <p className="text-xs text-gray-500 mt-1">Create a subject to begin organizing your curriculum.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700"
          >
            Create Subject
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {subjects.map((s) => (
            <div
              key={s.id}
              className="group relative flex flex-col justify-between rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 group-hover:scale-105 transition-transform">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div className="flex items-center gap-1.5 opacity-90">
                    <button
                      onClick={(e) => openEditModal(e, s)}
                      title="Edit Subject"
                      className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => openDeleteModal(e, s)}
                      title="Delete Subject"
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <Link href={`/subjects/${s.id}`}>
                  <h3 className="font-bold text-gray-900 hover:text-indigo-600 transition-colors">
                    {s.name}
                  </h3>
                  {s.description && (
                    <p className="mt-1 line-clamp-2 text-xs text-gray-500">
                      {s.description}
                    </p>
                  )}
                </Link>
              </div>

              <Link
                href={`/subjects/${s.id}`}
                className="mt-6 flex items-center justify-between border-t border-gray-100 pt-3 text-xs font-semibold text-indigo-600"
              >
                <span>View Units</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          ))}
        </div>
      )}

      {/* Create Subject Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">Create New Subject</h3>
            <form onSubmit={handleCreate} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Subject Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Principles of Management"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  placeholder="Subject scope, syllabus, or details"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !name.trim()}
                  className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Save Subject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Subject Modal */}
      {editingSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900">Edit Subject</h3>
            <form onSubmit={handleUpdate} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Subject Name
                </label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm focus:border-indigo-600 focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingSubject(null)}
                  className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating || !editName.trim()}
                  className="rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                  {updating ? "Saving..." : "Update Subject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Subject Confirmation Modal */}
      {deletingSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl border border-gray-200">
            <h3 className="text-base font-bold text-gray-900">Delete Subject?</h3>
            <p className="mt-2 text-xs text-gray-600">
              Are you sure you want to delete <span className="font-semibold text-gray-900">&ldquo;{deletingSubject.name}&rdquo;</span>? This will permanently remove all its units, uploaded resources, and progress.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeletingSubject(null)}
                className="rounded-xl border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? "Deleting..." : "Delete Permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
