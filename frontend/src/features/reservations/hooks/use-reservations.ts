import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  fetchReservations,
  fetchReservation,
  createReservation,
  fulfillReservation,
  cancelReservation,
} from "../api/reservations-api";
import type {
  ReservationListParams,
  CreateReservationPayload,
} from "../types/reservation.types";

const RESERVATIONS_KEY = "reservations";

export function useReservations(params: ReservationListParams = {}) {
  return useQuery({
    queryKey: [RESERVATIONS_KEY, params],
    queryFn: () => fetchReservations(params),
  });
}

export function useReservation(id: number) {
  return useQuery({
    queryKey: [RESERVATIONS_KEY, id],
    queryFn: () => fetchReservation(id),
    enabled: id > 0,
  });
}

export function useCreateReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateReservationPayload) =>
      createReservation(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [RESERVATIONS_KEY] });
    },
  });
}

export function useFulfillReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => fulfillReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [RESERVATIONS_KEY] });
    },
  });
}

export function useCancelReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => cancelReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [RESERVATIONS_KEY] });
    },
  });
}
