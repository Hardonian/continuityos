/**
 * Official TypeScript Client SDK for ContinuityOS.
 */

export type CorridorState =
  | 'HEALTHY'
  | 'DEGRADED'
  | 'OPEN_BUT_UNINSURABLE'
  | 'OPEN_BUT_NO_CARRIER_CAPACITY'
  | 'OPEN_BUT_NAVIGATION_UNTRUSTED'
  | 'OPEN_BUT_COMMUNICATIONS_DEGRADED'
  | 'RECOVERY_BACKLOGGED'
  | 'PHYSICALLY_CLOSED'
  | 'CLOSED'
  | 'UNKNOWN';

export interface CorridorStatus {
  corridor_id: string;
  effective_state: CorridorState;
  resilience_score: number;
  closure_reason?: string;
  reconciled_at: string;
}

export class ContinuityClient {
  private baseURL: string;
  private apiKey?: string;

  constructor(options: { baseURL?: string; apiKey?: string } = {}) {
    this.baseURL = options.baseURL || 'http://127.0.0.1:8082';
    this.apiKey = options.apiKey;
  }

  async getCorridorStatus(corridorId: string): Promise<CorridorStatus> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(`${this.baseURL}/v1/corridors/${corridorId}/status`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`ContinuityOS API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}
