import { Connection, PublicKey } from "@solana/web3.js";
import { getMint } from "@solana/spl-token";
import { DateTime } from "luxon";
import { config } from "./config";
import { createSellTransaction } from "./transactions";
import { CurrentTransaction } from "./types";
import Big from "big.js";

// State buffer to store vault updates with slot info
interface VaultState {
  reserve: bigint; // Use bigint to match getTokenAccountBalance
  slot: number;
}

// Minimum SOL liquidity threshold (e.g., 0.1 SOL)
const MINIMUM_SOL_LIQUIDITY = BigInt(1e8); // 0.1 SOL in lamports (10^9 lamports = 1 SOL)

// Get token balance using getTokenAccountBalance
async function getTokenBalance(connection: Connection, vaultPubkey: PublicKey): Promise<bigint> {
  const account = await connection.getTokenAccountBalance(vaultPubkey);
  const reserve = BigInt(account.value.amount);
  // console.log(`Vault ${vaultPubkey.toBase58()} - Amount: ${reserve}`);
  return reserve;
}

// Calculate PnL and return metrics
function calculatePnL(
  tokenReserve: bigint,
  solReserve: bigint,
  tokenDecimals: number,
  solDecimals: number,
  balance: number,
  solPaid: number,
  solPaidUSDC: number,
  initialPrice: number
): { unrealizedPnLPercentage: number; hrTradeTime: string; tokenCurrentPrice: number } {
  let tokenCurrentPrice = initialPrice;
  if (tokenReserve > 0 && solReserve > 0) {
    const price = new Big(String(solReserve))
      .div(new Big(10).pow(solDecimals))
      .div(new Big(String(tokenReserve)).div(new Big(10).pow(tokenDecimals)));
    tokenCurrentPrice = price.toNumber() * (solPaidUSDC / solPaid); // Convert to USDC
    if (tokenCurrentPrice > 1000 || tokenCurrentPrice < 0.0000001) {
      console.warn(`Suspicious price: ${tokenCurrentPrice} USDC - solReserve: ${solReserve}, tokenReserve: ${tokenReserve}`);
    }
  }

  const currentValue = tokenCurrentPrice * balance;
  const initialValue = solPaidUSDC;
  const unrealizedPnLUSDC = currentValue - initialValue;
  const unrealizedPnLPercentage = initialValue !== 0 ? (unrealizedPnLUSDC / initialValue) * 100 : 0;

  const iconPnl = unrealizedPnLUSDC > 0 ? "🟢" : "🔴";
  const hrTradeTime = DateTime.now().toLocal().toFormat("HH:mm:ss");

  // console.log("-------------------");
  // console.log(`tokenReserve: ${tokenReserve}`);
  // console.log(`solReserve: ${solReserve}`);
  // console.log(`tokenCurrentPrice (USDC): ${tokenCurrentPrice.toFixed(13)}`);
  console.log(`${iconPnl} - ${hrTradeTime} - Unrealized PnL: $${unrealizedPnLUSDC.toFixed(2)} (${unrealizedPnLPercentage.toFixed(2)}%)`);

  return { unrealizedPnLPercentage, hrTradeTime, tokenCurrentPrice };
}

export async function start(
  currentTransaction: CurrentTransaction,
  connection: Connection,
  getIsTransactionOpen: () => boolean,
  setIsTransactionOpen: (value: boolean) => void
): Promise<void> {
  console.log("swapDetails");
  console.log(currentTransaction);

  const { token, tokenTime, purchasePrice, balance, solPaid, solPaidUSDC, baseVault, quoteVault } = currentTransaction;
  const tokenMint = new PublicKey(token);
  const solMint = new PublicKey(config.liquidity_pool.wsol_pc_mint);

  // Correct vault assignment
  const tokenVault = new PublicKey(quoteVault as any); // Token vault (baseVault)
  const solVault = new PublicKey(baseVault as any);    // SOL vault (quoteVault)

  // Fetch decimals dynamically
  const tokenMintInfo = await getMint(connection, tokenMint);
  const solMintInfo = await getMint(connection, solMint);
  const tokenDecimals = tokenMintInfo.decimals; // e.g., 6 for DOB
  const solDecimals = solMintInfo.decimals;     // 9 for WSOL

  console.log("Monitoring PnL for:", token);
  console.log(`Purchase price: $${purchasePrice}`);
  console.log(`Amount: ${balance}`);
  console.log(`Amount Out USDC: $${solPaidUSDC}`);
  console.log(`Amount Out SOL: ${solPaid}`);
  console.log(`Base Vault (Token): ${baseVault}`);
  console.log(`Quote Vault (SOL): ${quoteVault}`);
  console.log(`Token Vault: ${tokenVault.toBase58()}`);
  console.log(`SOL Vault: ${solVault.toBase58()}`);

  // State buffer for synchronized updates
  const vaultState: { token: VaultState; sol: VaultState } = {
    token: { reserve: BigInt(0), slot: 0 },
    sol: { reserve: BigInt(0), slot: 0 },
  };
  const initialPrice = purchasePrice;

  // Track the latest processed slot and sell transaction state
  let lastProcessedSlot = 0;
  let sellTransactionInProgress = false;

  // Async handler for vault updates
  const handleVaultUpdate = async (
    vaultPubkey: PublicKey,
    isSolVault: boolean,
    slot: number,
    resolveMonitoring: (value?: void | PromiseLike<void>) => void // Add resolve callback
  ) => {
    try {
      const reserve = await getTokenBalance(connection, vaultPubkey);
      if (isSolVault) {
        vaultState.sol = { reserve, slot };
        // console.log(`Updated SOL Vault - Reserve: ${reserve}, Slot: ${slot}`);
      } else {
        vaultState.token = { reserve, slot };
        // console.log(`Updated Token Vault - Reserve: ${reserve}, Slot: ${slot}`);
      }

      // Check liquidity (SOL reserve) and abort if too low
      if (isSolVault && vaultState.sol.reserve < MINIMUM_SOL_LIQUIDITY) {
        console.warn(`⚠️ Liquidity too low in SOL vault (${vaultState.sol.reserve} lamports < ${MINIMUM_SOL_LIQUIDITY} lamports). Possible rug pull detected for ${token}. Aborting PnL monitoring.`);
        setIsTransactionOpen(false);
        resolveMonitoring(); // Exit the monitoring loop
        return;
      }

      // Calculate PnL if both vaults are at the same slot
      if (vaultState.token.slot === vaultState.sol.slot && vaultState.token.reserve > 0 && vaultState.sol.reserve > 0) {
        if (vaultState.token.slot > lastProcessedSlot) {
          lastProcessedSlot = vaultState.token.slot;
          if (getIsTransactionOpen() && !sellTransactionInProgress) {
            const { unrealizedPnLPercentage, hrTradeTime, tokenCurrentPrice } = calculatePnL(
              vaultState.token.reserve,
              vaultState.sol.reserve,
              tokenDecimals,
              solDecimals,
              balance,
              solPaid,
              solPaidUSDC,
              initialPrice
            );

            const amountIn = balance.toString().replace(".", "");
            if (unrealizedPnLPercentage >= config.sell.take_profit_percent) {
              sellTransactionInProgress = true;
              console.log(`Initiating Take Profit for ${token} at ${unrealizedPnLPercentage.toFixed(2)}%`);
              createSellTransaction(config.liquidity_pool.wsol_pc_mint, token, amountIn)
                .then((result) => {
                  if (result.success) {
                    console.log(`✅🟢 ${hrTradeTime}: Took profit for ${token}\nTx: ${result.tx}`);
                  } else {
                    console.log(`⚠️ ERROR when taking profit for ${token}: ${result.msg}`);
                  }
                })
                .catch((error) => console.log(`⚠️ ERROR when taking profit: ${error.message}`))
                .finally(() => {
                  sellTransactionInProgress = false;
                  setIsTransactionOpen(false);
                });
            } else if (unrealizedPnLPercentage <= -config.sell.stop_loss_percent) {
              sellTransactionInProgress = true;
              console.log(`Initiating Stop Loss for ${token} at ${unrealizedPnLPercentage.toFixed(2)}%`);
              createSellTransaction(config.liquidity_pool.wsol_pc_mint, token, amountIn)
                .then((result) => {
                  if (result.success) {
                    console.log(`✅🔴 ${hrTradeTime}: Triggered Stop Loss for ${token}\nTx: ${result.tx}`);
                  } else {
                    console.log(`⚠️ ERROR when triggering Stop Loss for ${token}: ${result.msg}`);
                  }
                })
                .catch((error) => console.log(`⚠️ ERROR when triggering Stop Loss: ${error.message}`))
                .finally(() => {
                  sellTransactionInProgress = false;
                  setIsTransactionOpen(false);
                });
            }
          } else if (sellTransactionInProgress) {
            console.log(`Sell transaction already in progress, skipping slot ${lastProcessedSlot}`);
          }
        }
      } else {
        // console.log(`Waiting for slot sync - Token Slot: ${vaultState.token.slot}, SOL Slot: ${vaultState.sol.slot}`);
      }
    } catch (error) {
      console.error(`Error fetching balance for ${vaultPubkey.toBase58()}: ${error instanceof Error ? error.message : error}`);
    }
  };

  // Subscribe to a vault and trigger async balance fetch
  const subscribeToVault = (
    vaultPubkey: PublicKey,
    connection: Connection,
    isSolVault: boolean,
    resolveMonitoring: (value?: void | PromiseLike<void>) => void
  ): number => {
    return connection.onAccountChange(
      vaultPubkey,
      (accountInfo, context) => {
        // Trigger async balance fetch on account change
        handleVaultUpdate(vaultPubkey, isSolVault, context.slot, resolveMonitoring);
      },
      "finalized"
    );
  };

  try {
    // Initial fetch of vault reserves
    const tokenAccount = await connection.getTokenAccountBalance(tokenVault);
    const solAccount = await connection.getTokenAccountBalance(solVault);

    // console.log("tokenAccount:", tokenAccount);
    // console.log("solAccount:", solAccount);

    if (tokenAccount) {
      vaultState.token = { reserve: BigInt(tokenAccount.value.amount), slot: 0 };
      // console.log("Initial tokenReserve:", vaultState.token.reserve);
    }
    if (solAccount) {
      vaultState.sol = { reserve: BigInt(solAccount.value.amount), slot: 0 };
      // console.log("Initial solReserve:", vaultState.sol.reserve);
    }

    // Initial PnL calculation with liquidity check
    if (vaultState.sol.reserve < MINIMUM_SOL_LIQUIDITY) {
      console.warn(`⚠️ Initial SOL liquidity too low (${vaultState.sol.reserve} lamports < ${MINIMUM_SOL_LIQUIDITY} lamports). Possible rug pull detected for ${token}. Aborting PnL monitoring.`);
      setIsTransactionOpen(false);
      return; // Exit early if initial liquidity is already gone
    }
    if (vaultState.token.reserve > 0 && vaultState.sol.reserve > 0) {
      calculatePnL(vaultState.token.reserve, vaultState.sol.reserve, tokenDecimals, solDecimals, balance, solPaid, solPaidUSDC, initialPrice);
    }

    // Subscribe to vault updates
    const subscriptionIds: number[] = [];
    await new Promise<void>((resolve) => {
      subscriptionIds.push(
        subscribeToVault(solVault, connection, true, resolve)
      );
      subscriptionIds.push(
        subscribeToVault(tokenVault, connection, false, resolve)
      );

      console.log(`Subscribed to vaults: SOL(${subscriptionIds[0]}), TOKEN(${subscriptionIds[1]})`);

      // Cleanup subscriptions when transaction closes or liquidity is removed
      const checkClosed = setInterval(() => {
        if (!getIsTransactionOpen()) {
          clearInterval(checkClosed);
          subscriptionIds.forEach((id) => connection.removeAccountChangeListener(id));
          console.log(`Unsubscribed from vaults: SOL(${subscriptionIds[0]}), TOKEN(${subscriptionIds[1]})`);
          resolve();
        }
      }, 100);
    });
  } catch (error) {
    console.error(`Error in monitorPnL: ${error instanceof Error ? error.message : error}`);
  } finally {
    setIsTransactionOpen(false);
  }
}



