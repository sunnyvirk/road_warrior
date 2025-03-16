import { config } from './config';
import {
  fetchTransactionDetails,
  createSwapTransaction,
  fetchCurrentTransaction
} from './transactions';
import { getRugCheckConfirmed } from "./rug-check";
import { CurrentTransaction } from './types';

export async function transaction(signature: string): Promise<false | CurrentTransaction> {
  console.log("=============================================");
  console.log("🔎 New Liquidity Pool found.");
  console.log("🔃 Fetching transaction details ...");

  const data = await fetchTransactionDetails(signature);
  if (!data) {
    console.log("⛔ Transaction aborted. No data returned.");
    console.log("🟢 Resuming looking for new tokens...\n");
    return false;
  }

  if (!data.solMint || !data.tokenMint) return false;

  if (data.tokenMint.trim().toLowerCase().endsWith("pump") && config.rug_check.ignore_pump_fun) {
    console.log("🚫 Transaction skipped. Ignoring Pump.fun.");
    console.log("🟢 Resuming looking for new tokens..\n");
    return false;
  }

  const isRugCheckPassed = await getRugCheckConfirmed(data.tokenMint);
  if (!isRugCheckPassed) {
    console.log("🚫 Rug Check not passed! Transaction aborted.");
    console.log("🟢 Resuming looking for new tokens...\n");
    return false;
  }

  console.log("Token found");
  console.log("👽 GMGN: https://gmgn.ai/sol/token/" + data.tokenMint);
  console.log("😈 BullX: https://neo.bullx.io/terminal?chainId=1399811149&address=" + data.tokenMint);

  await new Promise((resolve) => setTimeout(resolve, config.tx.swap_tx_initial_delay));

  const tx = await createSwapTransaction(data.solMint, data.tokenMint);
  if (!tx) {
    console.log("⛔ Transaction aborted.");
    console.log("🟢 Resuming looking for new tokens...\n");
    return false;
  }

  console.log("🚀 Swapping SOL for Token.");
  console.log("Swap Transaction: ", "https://solscan.io/tx/" + tx);

  const currentTransaction = await fetchCurrentTransaction(tx, data.tokenMint);
  if (currentTransaction) {
    return { ...currentTransaction, baseVault: data.baseVault, quoteVault: data.quoteVault, poolAddress: data.poolAddress };
  }
  return false;
}