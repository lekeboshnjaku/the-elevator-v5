// src/hooks/useWallet.ts
/**
 * React hook for Stake Engine wallet integration.
 * Manages wallet balance, loading, and error states.
 */
import { useState, useEffect, useCallback } from 'react';
import { walletApiClient, WalletBalanceResponse, WalletUpdateResponse } from '../api/wallet';

export interface UseWalletResult {
  balance: number | null;
  loading: boolean;
  error: string | null;
  refreshBalance: () => Promise<void>;
  handleTransaction: (amount: number) => Promise<void>;
  clearError: () => void;
}

export function useWallet(pollIntervalMs: number = 10000): UseWalletResult {
  const [balance, setBalance] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refreshBalance = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res: WalletBalanceResponse = await walletApiClient.getBalance();
      setBalance(res.balance);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch balance');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleTransaction = useCallback(async (amount: number) => {
    setLoading(true);
    setError(null);
    try {
      const res: WalletUpdateResponse = await walletApiClient.updateBalance(amount);
      setBalance(res.balance);
    } catch (err: any) {
      setError(err?.message || 'Transaction failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  // Initial load and polling
  useEffect(() => {
    refreshBalance();
    const interval = setInterval(refreshBalance, pollIntervalMs);
    return () => clearInterval(interval);
  }, [refreshBalance, pollIntervalMs]);

  // Optionally, listen to game events and refresh balance after bets, wins, etc.
  // (Integrate with game event system if available)

  return {
    balance,
    loading,
    error,
    refreshBalance,
    handleTransaction,
    clearError,
  };
}
