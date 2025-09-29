// src/api/wallet.ts
/**
 * Stake Engine Wallet API Client
 * Handles wallet-specific endpoints and session management for Stake Engine integration.
 */
import { ApiError } from '../../types';

export interface WalletBalanceResponse {
  balance: number;
  currency: string;
  updatedAt: string;
}

export interface WalletUpdateResponse {
  balance: number;
  currency: string;
  updatedAt: string;
  transactionId: string;
}

export interface WalletApiClient {
  getBalance(): Promise<WalletBalanceResponse>;
  updateBalance(amount: number): Promise<WalletUpdateResponse>;
  makeWalletRequest<T = any>(endpoint: string, method?: string, body?: any): Promise<T>;
  setSessionToken(token: string): void;
  setWalletUrl(url: string): void;
  formatCurrency(amount: number): string;
}

export class StakeEngineWalletApiClient implements WalletApiClient {
  private sessionToken: string | null = null;
  private walletUrl: string | null = null;
  private currencySymbol: string = '$';

  setSessionToken(token: string) {
    this.sessionToken = token;
  }

  setWalletUrl(url: string) {
    this.walletUrl = url;
  }

  formatCurrency(amount: number): string {
    return `${this.currencySymbol}${amount.toFixed(2)}`;
  }

  private getHeaders(): Record<string, string> {
    if (!this.sessionToken) throw new ApiError('Session token not set', 401);
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${this.sessionToken}`,
    };
  }

  async makeWalletRequest<T = any>(endpoint: string, method: string = 'GET', body?: any): Promise<T> {
    if (!this.walletUrl) throw new ApiError('Wallet URL not set', 500);
    const url = `${this.walletUrl}${endpoint}`;
    const headers = this.getHeaders();
    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new ApiError(data?.message || 'Wallet API error', response.status);
      }
      return data as T;
    } catch (error: any) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(error?.message || 'Network error', 500);
    }
  }

  async getBalance(): Promise<WalletBalanceResponse> {
    const data = await this.makeWalletRequest<WalletBalanceResponse>('/balance', 'GET');
    if (!data || typeof data.balance !== 'number') {
      throw new ApiError('Invalid balance response', 502);
    }
    return data;
  }

  async updateBalance(amount: number): Promise<WalletUpdateResponse> {
    const data = await this.makeWalletRequest<WalletUpdateResponse>('/balance', 'POST', { amount });
    if (!data || typeof data.balance !== 'number') {
      throw new ApiError('Invalid update balance response', 502);
    }
    return data;
  }
}

export const walletApiClient = new StakeEngineWalletApiClient();
