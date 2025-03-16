import WebSocket from "ws";
import { Connection, PublicKey } from '@solana/web3.js';
import { WebSocketRequest, CurrentTransaction } from "./types";
import { config } from "./config";
import { validateEnv } from "./utils/env-validator";

import * as PoolCreation from "./pool-creation"; 
import * as Process from "./process";
import * as Monitor from "./monitor";
import { connect } from "http2";

// State to track the open transaction
let isTransactionOpen = false;
let currentTransaction: false | CurrentTransaction; // Adjust type based on your swapDetails structure

// Function used to open our websocket connection
function sendSubscribeRequest(ws: WebSocket): void {
  const request: WebSocketRequest = {
    jsonrpc: "2.0",
    id: 1,
    method: "logsSubscribe",
    params: [
      {
        mentions: [config.liquidity_pool.radiyum_program_id],
      },
      {
        commitment: "processed", // Can use finalized to be more accurate.
      },
    ],
  };
  ws.send(JSON.stringify(request));
}

// Websocket Handler for listening to the Solana logSubscribe method
let init = false;
async function websocketHandler(): Promise<void> {
  // Load environment variables from the .env file
  const env = validateEnv();

  // Create a WebSocket connection
  let ws: WebSocket | null = new WebSocket(env.WSS_URI);
  if (!init) console.clear();

  const connection = new Connection((process.env.HTTPS_URI as any), {
    wsEndpoint: process.env.WSS_URI,
    commitment: 'confirmed',
  });

  // Send subscription to the websocket once the connection is open
  ws.on("open", () => {
    // Subscribe
    if (ws) sendSubscribeRequest(ws); // Send a request once the WebSocket is open
    console.log("\n🔓 WebSocket is open and listening.");
    init = true;
  }); 

  // Logic for the message event for the .on event listener
  ws.on("message", async (data: WebSocket.Data) => {
    try {
      const jsonString = data.toString(); // Convert data to a string
      const parsedData = JSON.parse(jsonString); // Parse the JSON string

      // Skip if a transaction is already open
      if (isTransactionOpen) {
        return;
      }

      // Handle subscription response
      if (parsedData.result !== undefined && !parsedData.error) {
        console.log("✅ Subscription confirmed");
        return;
      }

      // Only log RPC errors for debugging
      if (parsedData.error) {
        console.error("🚫 RPC Error:", parsedData.error);
        return;
      }

      const signature = PoolCreation.verify(parsedData);
      if (!signature) return;

      // Set the lock
      isTransactionOpen = true;
      console.log("⏳ Processing transaction:", signature);
      
      try {
        currentTransaction = await Process.transaction(signature);
        
        if (currentTransaction) {
          console.log("🟢 Transaction processed successfully.");
          // Pause for 5 seconds before starting to monitor PnL
          await new Promise((resolve) => setTimeout(resolve, 10000));
          // start monitoring
          await Monitor.start(currentTransaction, connection, () => isTransactionOpen, (value) => isTransactionOpen = value);
        }
      } catch (error) {
        console.error("Error processing transaction:", error);
      } finally {
        // Reset state when done
        console.log("🟢 Resuming looking for new tokens...");
        isTransactionOpen = false;
        currentTransaction = false;
      }

    } catch (error) {
      console.error("💥 Error processing message:", {
        error: error instanceof Error ? error.message : "Unknown error",
        timestamp: new Date().toISOString(),
      });
    }
  });

  ws.on("error", (err: Error) => {
    console.error("WebSocket error:", err);
  });

  ws.on("close", (why) => {
    console.log(why);
    console.log("📴 WebSocket connection closed, cleaning up...");
    if (ws) {
      ws.removeAllListeners();
      ws = null;
    }
    console.log("🔄 Attempting to reconnect in 5 seconds...");
    setTimeout(websocketHandler, 5000);
  });
}

// Start Socket Handler
websocketHandler().catch((err) => {
  console.error(err.message);
});







// import Big from "big.js";



// import { LIQUIDITY_STATE_LAYOUT_V4, WSOL } from "@raydium-io/raydium-sdk";



// async function main0() {

//   // const connection = new Connection(["https://api.mainnet-beta.solana.com"], "confirmed");



//   const connection = new Connection("process.env.HTTPS_URI", {
//     commitment: 'confirmed',
//   });


//   const conn = connection;

//   const poolAddress = new PublicKey("3zvuhrmWtcMRs41KEtwfx1wNnkXsbivot7AtoA5dvx2E");

//   const poolRawState = await conn.getAccountInfo(poolAddress);
//   if (poolRawState) {


//     const poolState = LIQUIDITY_STATE_LAYOUT_V4.decode(poolRawState.data);

//     const poolBaseAndQuoteSwapped = poolState.baseMint.toBase58() === WSOL.mint;

//     const tokenVault = poolBaseAndQuoteSwapped ? poolState.quoteVault : poolState.baseVault;
//     const tokenDecimals = Number(poolBaseAndQuoteSwapped ? poolState.quoteDecimal : poolState.baseDecimal);
//     const refVault = poolBaseAndQuoteSwapped ? poolState.baseVault : poolState.quoteVault;
//     const refDecimals = Number(poolBaseAndQuoteSwapped ? poolState.baseDecimal : poolState.quoteDecimal);

//     const vaults = {
//       token: {
//         address: tokenVault.toBase58(),
//         decimals: tokenDecimals,
//         balance: BigInt((await conn.getTokenAccountBalance(tokenVault)).value.amount),
//       },
//       ref: {
//         address: refVault.toBase58(),
//         decimals: refDecimals,
//         balance: BigInt((await conn.getTokenAccountBalance(refVault)).value.amount),
//       },
//     };

//     console.log('====================================');
//     console.log('vaults');
//     console.log(vaults);

//     function amountToBig(amount: bigint, decimals: number) {
//       return new Big(String(amount)).div(new Big(10).pow(decimals));
//     }
//     function logPrice() {
//       const price =
//         amountToBig(vaults.ref.balance, vaults.ref.decimals)
//           .div(amountToBig(vaults.token.balance, vaults.token.decimals));


//       const tokenCurrentPrice = (price as any) * (1.3262693100000003 / 0.01);

//       console.log('tokenCurrentPrice', tokenCurrentPrice.toFixed(13));

//       console.log(`[${new Date().toISOString()}]    price: ${price.toFixed(10)} SOL`);
//     }

//     logPrice();

//     console.log('====================================');

//   }

// }

// main0().catch(console.error);





// async function main() {
//   const connection = new Connection("https://api.mainnet-beta.solana.com", "confirmed");
//   const swapDetails = {
//     token: 'Ba4HgVv5mr3Cz1PJr4s9PmemcPSqB6GPfcdev5xppump',
//     tokenTime: 1742027365,
//     purchasePrice: 0.0006562924707918668,
//     balance: 2021.812285,
//     solPaid: 0.01,
//     solPaidUSDC: 1.3269001800000002,
//     baseVault: 'H6hgxFc8uYxtRcSiPsuLcnW1eFANkGGCNN9Xe3iWxiyG',
//     quoteVault: 'FvHwEZGVUW2VfYwTJ26boywb8ES216DC4sJgJbfJZqLM',
//     poolAddress: '3zvuhrmWtcMRs41KEtwfx1wNnkXsbivot7AtoA5dvx2E'
//   };
//   let isTransactionOpen = true;
//   await Monitor.start(swapDetails, connection, () => isTransactionOpen, (value) => (isTransactionOpen = value));
// }

// main().catch(console.error);
