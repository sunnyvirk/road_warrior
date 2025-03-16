import axios from "axios";
import { Connection, Keypair, VersionedTransaction, PublicKey } from "@solana/web3.js";
import { Wallet } from "@project-serum/anchor";


import { getAssociatedTokenAddress } from "@solana/spl-token";



import bs58 from "bs58";
import dotenv from "dotenv";
import { config } from "./config";
import {
  TransactionDetailsResponse,
  MintsDataReponse,
  QuoteResponse,
  SerializedQuoteResponse,
  createSellTransactionResponse,
  CurrentTransaction,
  WebSocketRequest
} from "./types";

// Load environment variables from the .env file
dotenv.config();

const headers = { "Content-Type": "application/json" };

export async function fetchTransactionDetails(signature: string): Promise<MintsDataReponse | null> {
  const txUrl = process.env.HTTPS_URI || "";
  const maxRetries = config.tx.fetch_tx_max_retries;
  let retryCount = 0;

  console.log("Waiting " + config.tx.fetch_tx_initial_delay / 1000 + " seconds for transaction to be confirmed...");
  await new Promise((resolve) => setTimeout(resolve, config.tx.fetch_tx_initial_delay));

  while (retryCount < maxRetries) {
    try {
      console.log(`Attempt ${retryCount + 1} of ${maxRetries} to fetch transaction details...`);

      const requestBody: WebSocketRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'getTransaction',
        params: [
          signature,
          {
            maxSupportedTransactionVersion: 0,
            encoding: 'jsonParsed',
            commitment: 'confirmed'
          }
        ]
      };

      const response = await axios.post<any>(
        txUrl,
        requestBody,
        { headers, timeout: config.tx.get_timeout }
      );

      if (!response.data) {
        throw new Error("No response data received");
      }

      const transaction = response.data.result.transaction.message;
      const meta = response.data.result.meta;

      if (!transaction) {
        throw new Error("Transaction not found");
      }

      const instructions = transaction.instructions;
      if (!instructions || !Array.isArray(instructions) || instructions.length === 0) {
        throw new Error("No instructions found in transaction");
      }

      const instruction = instructions.find((ix) => ix.programId === config.liquidity_pool.radiyum_program_id);
      if (!instruction || !instruction.accounts) {
        throw new Error("No market maker instruction found");
      }
      if (!Array.isArray(instruction.accounts) || instruction.accounts.length < 12) {
        throw new Error("Invalid accounts array in instruction");
      }

      // Extract vaults (consistent for pool creation and swaps)
      const baseVault = instruction.accounts[11]; // Token vault
      const quoteVault = instruction.accounts[10]; // SOL vault

      const poolAddress = instruction.accounts[4]; // Pool address

      // Pool creation: Mints at indices 8 (quote/SOL) and 9 (base/token)
      let solMint = "";
      let tokenMint = "";
      const quoteMint = instruction.accounts[8]; // SOL mint
      const baseMint = instruction.accounts[9];  // Token mint

      if (quoteMint === config.liquidity_pool.wsol_pc_mint) {
        solMint = quoteMint;
        tokenMint = baseMint;
      }

      // Fallback to postTokenBalances (for swaps or if pool creation layout differs)
      if ((!solMint || !tokenMint) && meta && meta.postTokenBalances) {
        meta.postTokenBalances.forEach((balance: any) => {
          if (balance.mint === config.liquidity_pool.wsol_pc_mint) {
            solMint = balance.mint;
          } else if (balance.mint && balance.mint !== config.liquidity_pool.wsol_pc_mint && balance.mint !== instruction.accounts[7]) {
            tokenMint = balance.mint; // Exclude LP mint (index 7)
          }
        });
      }

      if (!solMint || !tokenMint) {
        throw new Error("Required mints not found");
      }

      console.log("Successfully fetched transaction details!");
      console.log(`SOL Mint: ${solMint}`);
      console.log(`New Token Mint: ${tokenMint}`);
      console.log(`Base Vault: ${baseVault}`);
      console.log(`Quote Vault: ${quoteVault}`);

      const displayData: MintsDataReponse = {
        solMint,
        tokenMint,
        baseVault,
        quoteVault,
        poolAddress
      };

      return displayData;
    } catch (error: any) {
      console.log(`Attempt ${retryCount + 1} failed: ${error.message}`);
      retryCount++;
      if (retryCount < maxRetries) {
        const delay = Math.min(4000 * Math.pow(1.5, retryCount), 15_000);
        console.log(`Waiting ${delay / 1000} seconds before next attempt...`);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  console.log("All attempts to fetch transaction details failed");
  return null;
}


export async function createSwapTransaction(solMint: string, tokenMint: string): Promise<string | null> {
  const quoteUrl = process.env.JUP_HTTPS_QUOTE_URI || "";
  const swapUrl = process.env.JUP_HTTPS_SWAP_URI || "";
  const rpcUrl = process.env.HTTPS_URI || "";
  const priceUrl = process.env.JUP_HTTPS_PRICE_URI || "";

  let quoteResponseData: QuoteResponse | null = null;
  let serializedQuoteResponseData: SerializedQuoteResponse | null = null;
  const connection = new Connection(rpcUrl);
  const myWallet = new Wallet(Keypair.fromSecretKey(bs58.decode(process.env.PRIV_KEY_WALLET || "")));

  // Get Swap Quote
  let retryCount = 0;
  while (retryCount < config.swap.token_not_tradable_400_error_retries) {
    try {
      // Request a quote in order to swap SOL for new token
      const quoteResponse = await axios.get<QuoteResponse>(quoteUrl, {
        params: {
          inputMint: solMint,
          outputMint: tokenMint,
          amount: config.swap.amount,
          slippageBps: config.swap.slippageBps,
        },
        timeout: config.tx.get_timeout,
      });

      if (!quoteResponse.data) return null;

      if (config.swap.verbose_log && config.swap.verbose_log === true) {
        console.log("\nVerbose log:");
        console.log(quoteResponse.data);
      }

      quoteResponseData = quoteResponse.data; // Store the successful response
      break;
    } catch (error: any) {
      // Retry when error is TOKEN_NOT_TRADABLE
      if (error.response && error.response.status === 400) {
        const errorData = error.response.data;
        if (errorData.errorCode === "TOKEN_NOT_TRADABLE") {
          retryCount++;
          await new Promise((resolve) => setTimeout(resolve, config.swap.token_not_tradable_400_error_delay));
          continue; // Retry
        }
      }

      // Throw error (null) when error is not TOKEN_NOT_TRADABLE
      console.error("Error while requesting a new swap quote:", error.message);
      if (config.swap.verbose_log && config.swap.verbose_log === true) {
        console.log("Verbose Error Message:");
        if (error.response) {
          // Server responded with a status other than 2xx
          console.error("Error Status:", error.response.status);
          console.error("Error Status Text:", error.response.statusText);
          console.error("Error Data:", error.response.data); // API error message
          console.error("Error Headers:", error.response.headers);
        } else if (error.request) {
          // Request was made but no response was received
          console.error("No Response:", error.request);
        } else {
          // Other errors
          console.error("Error Message:", error.message);
        }
      }
      return null;
    }
  }

  if (quoteResponseData) console.log("✅ Swap quote recieved.");


  // Serialize the quote into a swap transaction that can be submitted on chain
  try {
    if (!quoteResponseData) return null;

    const swapResponse = await axios.post<SerializedQuoteResponse>(
      swapUrl,
      JSON.stringify({
        // quoteResponse from /quote api
        quoteResponse: quoteResponseData,
        // user public key to be used for the swap
        userPublicKey: myWallet.publicKey.toString(),
        // auto wrap and unwrap SOL. default is true
        wrapAndUnwrapSol: true,
        //dynamicComputeUnitLimit: true, // allow dynamic compute limit instead of max 1,400,000
        dynamicSlippage: {
          // This will set an optimized slippage to ensure high success rate
          maxBps: 300, // Make sure to set a reasonable cap here to prevent MEV
        },
        prioritizationFeeLamports: {
          priorityLevelWithMaxLamports: {
            maxLamports: config.swap.prio_fee_max_lamports,
            priorityLevel: config.swap.prio_level,
          },
        },
      }),
      {
        headers: headers,
        timeout: config.tx.get_timeout,
      }
    );
    if (!swapResponse.data) return null;

    if (config.swap.verbose_log && config.swap.verbose_log === true) {
      console.log(swapResponse.data);
    }

    serializedQuoteResponseData = swapResponse.data; // Store the successful response
  } catch (error: any) {
    console.error("Error while sending the swap quote:", error.message);
    if (config.swap.verbose_log && config.swap.verbose_log === true) {
      console.log("Verbose Error Message:");
      if (error.response) {
        // Server responded with a status other than 2xx
        console.error("Error Status:", error.response.status);
        console.error("Error Status Text:", error.response.statusText);
        console.error("Error Data:", error.response.data); // API error message
        console.error("Error Headers:", error.response.headers);
      } else if (error.request) {
        // Request was made but no response was received
        console.error("No Response:", error.request);
      } else {
        // Other errors
        console.error("Error Message:", error.message);
      }
    }
    return null;
  }

  if (serializedQuoteResponseData) console.log("✅ Swap quote serialized.");

  // deserialize, sign and send the transaction
  try {
    if (!serializedQuoteResponseData) return null;
    const swapTransactionBuf = Buffer.from(serializedQuoteResponseData.swapTransaction, "base64");
    var transaction = VersionedTransaction.deserialize(swapTransactionBuf);

    // sign the transaction
    transaction.sign([myWallet.payer]);

    // get the latest block hash
    // const latestBlockHash = await connection.getLatestBlockhash();

    // Execute the transaction
    const rawTransaction = transaction.serialize();
    const txid = await connection.sendRawTransaction(rawTransaction, {
      skipPreflight: true, // If True, This will skip transaction simulation entirely.
      maxRetries: 2
    });

    // Return null when no tx was returned
    if (!txid) {
      console.log("🚫 No id received for sent raw transaction.");
      return null;
    }

    if (txid) console.log("✅ Raw transaction id received.");

    let confirmed = false;
    let attempts = 0;
    while (!confirmed && attempts < 3) {
      const status = await connection.getSignatureStatuses([txid], {
        "searchTransactionHistory": true
      });
      if (status.value && status.value[0] && status.value[0].confirmationStatus === 'confirmed') {
        confirmed = true;
      } else {
        attempts++;
        // wait before trying again
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }

    if (txid) console.log("🔎 Checking transaction confirmation ...");

    // Return null when an error occured when confirming the transaction
    if (!confirmed) {
      console.log("🚫 Transaction confirmation failed.");
      return null;
    } else {
      console.log("✅ Transaction confirmed.");
    }

    return txid;

  } catch (error: any) {
    console.error("Error while signing and sending the transaction:", error.message);
    if (config.swap.verbose_log && config.swap.verbose_log === true) {
      console.log("Verbose Error Message:");
      if (error.response) {
        // Server responded with a status other than 2xx
        console.error("Error Status:", error.response.status);
        console.error("Error Status Text:", error.response.statusText);
        console.error("Error Data:", error.response.data); // API error message
        console.error("Error Headers:", error.response.headers);
      } else if (error.request) {
        // Request was made but no response was received
        console.error("No Response:", error.request);
      } else {
        // Other errors
        console.error("Error Message:", error.message);
      }
    }
    return null;
  }
}

export async function fetchCurrentTransaction(txid: string, tokenMint: string): Promise<CurrentTransaction | false> {
  const txUrl = process.env.HTTPS_URI || "";
  const priceUrl = process.env.JUP_HTTPS_PRICE_URI || "";

  const myWallet = new Wallet(Keypair.fromSecretKey(bs58.decode(process.env.PRIV_KEY_WALLET || "")));

  // Inside fetchSwapDetails
  const solMint = new PublicKey(config.liquidity_pool.wsol_pc_mint);
  const walletPubkey = myWallet.publicKey;
  const wsolAta = await getAssociatedTokenAddress(solMint, walletPubkey);

  try {
    const requestBody = {
      jsonrpc: "2.0",
      id: 1,
      method: "getTransaction",
      params: [
        txid,
        {
          maxSupportedTransactionVersion: 0,
          encoding: "jsonParsed",
          commitment: "confirmed",
        },
      ],
    };
  
    const response = await axios.post<any>(txUrl, requestBody, {
      headers,
      timeout: config.tx.get_timeout,
    });
  
    if (!response.data || !response.data.result) {
      console.log("⛔ Could not fetch swap details: No response received from API.");
      return false;
    }
  
    const transaction = response.data.result;
  
    // Get SOL price in USD
    const solMint = config.liquidity_pool.wsol_pc_mint; // e.g., "So11111111111111111111111111111111111111112"
    const priceResponse = await axios.get<any>(priceUrl, {
      params: { ids: solMint },
      timeout: config.tx.get_timeout,
    });
  
    if (!priceResponse.data.data[solMint]?.price) {
      console.log("⛔ Could not fetch SOL price.");
      return false;
    }
  
    const solUsdcPrice = priceResponse.data.data[solMint].price;
  
    // Find the SOL spent
    let solSpent = 0;
    for (const inner of transaction.meta.innerInstructions) {
      for (const instr of inner.instructions) {
        if (
          instr.parsed?.type === "transfer" &&
          instr.parsed.info.source === wsolAta.toString() &&
          instr.program === "spl-token"
        ) {
          solSpent = parseInt(instr.parsed.info.amount) / 1_000_000_000;
          break;
        }
      }
      if (solSpent) break;
    }
  
    // Find the tokens received (from postTokenBalances)
    let tokensReceived = 0;
    for (const balance of transaction.meta.postTokenBalances) {
      if (
        balance.mint === tokenMint &&
        balance.owner === myWallet.publicKey.toString()
      ) {
        tokensReceived = parseFloat(balance.uiTokenAmount.uiAmountString);
        break;
      }
    }
  
    if (!solSpent || !tokensReceived) {
      console.log("⛔ Could not calculate swap details from transaction.");
      return false;
    }
  
    // Calculate purchase price and additional fields
    const purchasePriceSol = solSpent / tokensReceived; // Price per token in SOL
    const purchasePriceUsd = purchasePriceSol * solUsdcPrice; // Price per token in USD
    const solPaidUsdc = solSpent * solUsdcPrice; // Total SOL paid in USD
  
    const swapTransactionData: CurrentTransaction = {
      token: tokenMint,
      tokenTime: transaction.blockTime,
      purchasePrice: purchasePriceUsd, // Value of each token in USD when bought
      balance: tokensReceived,         // Amount of tokens bought
      solPaid: solSpent,              // Amount of SOL paid
      solPaidUSDC: solPaidUsdc,       // Amount of SOL paid in USD
    };
  
    return swapTransactionData;
  } catch (error: any) {
    console.error("Error during request:", error.message);
    return false;
  }
}

export async function createSellTransaction(solMint: string, tokenMint: string, amount: string): Promise<createSellTransactionResponse> {
  const quoteUrl = process.env.JUP_HTTPS_QUOTE_URI || "";
  const swapUrl = process.env.JUP_HTTPS_SWAP_URI || "";
  const rpcUrl = process.env.HTTPS_URI || "";
  const myWallet = new Wallet(Keypair.fromSecretKey(bs58.decode(process.env.PRIV_KEY_WALLET || "")));
  const connection = new Connection(rpcUrl);

  try {
    // Check token balance using RPC connection
    const tokenAccounts = await connection.getParsedTokenAccountsByOwner(myWallet.publicKey, {
      mint: new PublicKey(tokenMint),
    });

    //Check if token exists in wallet with non-zero balance
    const totalBalance = tokenAccounts.value.reduce((sum, account) => {
      const tokenAmount = account.account.data.parsed.info.tokenAmount.amount;
      return sum + BigInt(tokenAmount); // Use BigInt for precise calculations
    }, BigInt(0));

    // Verify returned balance
    if (totalBalance <= 0n) {
      throw new Error(`Token has 0 balance - Already sold elsewhere. Removing from tracking.`);
    }

    // Verify amount with tokenBalance
    if (totalBalance !== BigInt(amount)) {
      // should I throw or update my in memory balance?
      throw new Error(`Wallet and tracker balance mismatch. Sell manually and token will be removed during next price check.`);
    }

    // Request a quote in order to swap SOL for new token
    const quoteResponse = await axios.get<QuoteResponse>(quoteUrl, {
      params: {
        inputMint: tokenMint,
        outputMint: solMint,
        amount: amount,
        slippageBps: config.sell.slippageBps,
      },
      timeout: config.tx.get_timeout,
    });

    // Throw error if no quote was received
    if (!quoteResponse.data) {
      throw new Error("No valid quote for selling the token was received from Jupiter!");
    }

    // Serialize the quote into a swap transaction that can be submitted on chain
    const swapTransaction = await axios.post<SerializedQuoteResponse>(
      swapUrl,
      JSON.stringify({
        // quoteResponse from /quote api
        quoteResponse: quoteResponse.data,
        // user public key to be used for the swap
        userPublicKey: myWallet.publicKey.toString(),
        // auto wrap and unwrap SOL. default is true
        wrapAndUnwrapSol: true,
        //dynamicComputeUnitLimit: true, // allow dynamic compute limit instead of max 1,400,000
        dynamicSlippage: {
          // This will set an optimized slippage to ensure high success rate
          maxBps: 300, // Make sure to set a reasonable cap here to prevent MEV
        },
        prioritizationFeeLamports: {
          priorityLevelWithMaxLamports: {
            maxLamports: config.sell.prio_fee_max_lamports,
            priorityLevel: config.sell.prio_level,
          },
        },
      }),
      {
        headers,
        timeout: config.tx.get_timeout,
      }
    );

    // Throw error if no quote was received
    if (!swapTransaction.data) {
      throw new Error("No valid swap transaction was received from Jupiter!");
    }

    // deserialize the transaction
    const swapTransactionBuf = Buffer.from(swapTransaction.data.swapTransaction, "base64");
    var transaction = VersionedTransaction.deserialize(swapTransactionBuf);

    // sign the transaction
    transaction.sign([myWallet.payer]);

    // Execute the transaction
    const rawTransaction = transaction.serialize();
    const txid = await connection.sendRawTransaction(rawTransaction, {
      skipPreflight: true, // If True, This will skip transaction simulation entirely.
      maxRetries: 2,
    });

    // Return null when no tx was returned
    if (!txid) {
      throw new Error("Could not send transaction that was signed and serialized!");
    }

    if (txid) console.log("✅ Raw transaction id received.");

    let confirmed = false;
    let attempts = 0;
    while (!confirmed && attempts < 3) {
      const status = await connection.getSignatureStatuses([txid], {
        "searchTransactionHistory": true
      });
      if (status.value && status.value[0] && status.value[0].confirmationStatus === 'confirmed') {
        confirmed = true;
      } else {
        attempts++;
        // wait before trying again
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }

    if (txid) console.log("🔎 Checking transaction confirmation ...");

    // Return null when an error occured when confirming the transaction
    if (!confirmed) {
      console.log("🚫 Transaction confirmation failed.");
      throw new Error("Transaction was not successfully confirmed!");
    } else {
      console.log("✅ Transaction confirmed.");
    }

    return {
      success: true,
      msg: null,
      tx: txid,
    };
  } catch (error: any) {
    return {
      success: false,
      msg: error instanceof Error ? error.message : "Unknown error",
      tx: null,
    };
  }
}