/**
 * @output-dir src/hooks
 * @file-naming use{Resource}.js
 *
 * PATTERN: React Query hooks for a resource
 *
 * DEMONSTRATES:
 * - useQuery for reads
 * - useMutation for writes
 * - Cache invalidation on mutation
 * - Pagination support
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '../api/users.api';

const QUERY_KEY = 'users';

export function useUsers(page = 1, limit = 20) {
  return useQuery({
    queryKey: [QUERY_KEY, page, limit],
    queryFn:  () => usersApi.getAll(page, limit),
  });
}

export function useUser(id) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn:  () => usersApi.getById(id),
    enabled:  !!id,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => usersApi.create(data),
    onSuccess:  () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => usersApi.update(id, data),
    onSuccess:  () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => usersApi.delete(id),
    onSuccess:  () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}