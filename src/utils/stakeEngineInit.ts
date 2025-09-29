// src/utils/stakeEngineInit.ts
/**
 * Stake Engine session initialization utilities.
 * Handles session config, extraction, and validation for Stake Engine integration.
 */
import { ApiError } from '../../types';

export interface StakeSessionConfig {
  sessionToken: string;
  rgsUrl: string;
  gameId?: string;
  vendorId?: string;
  headers?: Record<string, string>;
}

/**
 * Extract session parameters from URL or global context.
 */
export function extractSessionParams(): Partial<StakeSessionConfig> {
  const params = new URLSearchParams(window.location.search);
  const sessionToken = params.get('sessionToken') || '';
  const rgsUrl = params.get('rgsUrl') || '';
  const gameId = params.get('gameId') || '';
  const vendorId = params.get('vendorId') || '';
  return {
    sessionToken,
    rgsUrl,
    gameId,
    vendorId,
  };
}

/**
 * Validate session config for required fields.
 */
export function validateSessionConfig(config: Partial<StakeSessionConfig>): asserts config is StakeSessionConfig {
  if (!config.sessionToken || !config.rgsUrl) {
    throw new ApiError('Missing sessionToken or rgsUrl in session config', 400);
  }
}

/**
 * Initialize Stake Engine session and set headers.
 */
export function initializeSession(config: StakeSessionConfig) {
  validateSessionConfig(config);
  const headers: Record<string, string> = {
    Authorization: `Bearer ${config.sessionToken}`,
  };
  if (config.gameId) headers['X-Stake-Game-Id'] = config.gameId;
  if (config.vendorId) headers['X-Stake-Vendor-Id'] = config.vendorId;
  if (config.headers) Object.assign(headers, config.headers);
  // Example: set up API clients with session
  // rgsApiService.initialize(config.sessionToken, config.rgsUrl, { headers });
  // walletApiClient.setSessionToken(config.sessionToken);
  // walletApiClient.setWalletUrl(config.rgsUrl);
  return headers;
}
