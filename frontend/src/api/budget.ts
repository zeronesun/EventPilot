import { fetchClient } from './client';

export interface BudgetItem {
  id: string;
  event: string;
  category_name: string;
  name: string;
  estimated_amount: number;
  actual_amount: number;
  variance: number;
  responsible?: string;
  responsible_name?: string;
  status: 'pending' | 'in_progress' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface CreateBudgetItemRequest {
  event: string;
  category_name: string;
  name: string;
  estimated_amount: number;
  actual_amount?: number;
  responsible?: string;
  status?: string;
}

export interface UpdateBudgetItemRequest {
  category_name?: string;
  name?: string;
  estimated_amount?: number;
  actual_amount?: number;
  responsible?: string;
  status?: string;
}

export async function createBudgetItem(data: CreateBudgetItemRequest): Promise<BudgetItem> {
  const client = fetchClient();
  const response = await client.post('/events/budget-items/', data);
  return response;
}

export async function getBudgetItems(eventId?: string): Promise<BudgetItem[]> {
  const client = fetchClient();
  const params = eventId ? { event: eventId } : {};
  const response = await client.get('/events/budget-items/', params);
  return response;
}

export async function getBudgetItem(id: string): Promise<BudgetItem> {
  const client = fetchClient();
  const response = await client.get(`/events/budget-items/${id}/`);
  return response;
}

export async function updateBudgetItem(
  id: string,
  data: UpdateBudgetItemRequest
): Promise<BudgetItem> {
  const client = fetchClient();
  const response = await client.patch(`/events/budget-items/${id}/`, data);
  return response;
}

export async function deleteBudgetItem(id: string): Promise<void> {
  const client = fetchClient();
  await client.delete(`/events/budget-items/${id}/`);
}
