// src/components/Balance.tsx
/**
 * Balance display component for Stake Engine wallet integration.
 * Shows balance, loading, and error states with cyan/neon styling.
 */
import React from 'react';

interface BalanceProps {
  balance: number | null;
  formatCurrency: (amount: number) => string;
  className?: string;
  loading?: boolean;
  error?: string | null;
}

const Balance: React.FC<BalanceProps> = ({ balance, formatCurrency, className = '', loading = false, error = null }) => {
  return (
    <div
      className={`flex items-center justify-center px-4 py-2 rounded-lg bg-[#0b0f1c] border border-cyan-400/60 shadow-[0_0_10px_rgba(0,246,255,0.25)] text-cyan-300 font-[Orbitron] text-lg sm:text-xl tracking-wider select-none transition-all duration-200 ease-out ${className}`}
      aria-live="polite"
      aria-busy={loading}
      aria-label="Wallet balance"
    >
      {loading ? (
        <span className="animate-pulse text-cyan-200">Loading...</span>
      ) : error ? (
        <span className="text-red-400">{error}</span>
      ) : (
        <span className="drop-shadow-[0_0_6px_rgba(0,246,255,0.7)]">{balance !== null ? formatCurrency(balance) : '--'}</span>
      )}
    </div>
  );
};

export default Balance;
